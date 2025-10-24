import anthropic
import pyautogui
import subprocess
import time
import os
import json
import argparse
from PIL import ImageGrab

TRAJECTORY_DIR = "/Users/martasumyk/Desktop/Thesis/baseline/anthropic_trajectories" # where to save screenshots + reasonings
os.makedirs(TRAJECTORY_DIR, exist_ok=True)

client = anthropic.Anthropic()

AI_WIDTH, AI_HEIGHT = 1024, 768
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
MAX_REPEATS = 3 # maximum number of repeated cycles
MAX_STEPS = 20 # if task is not done in MAX_STEPS times - just finish it


# -------------------------------
# Helpers
# -------------------------------
def next_task_dir(base_dir: str) -> str:
    """Find next task_{NNN} directory name."""
    existing = [d for d in os.listdir(base_dir) if d.startswith("task_")]
    nums = []
    for d in existing:
        try:
            nums.append(int(d.split("_")[1]))
        except Exception:
            pass
    nxt = (max(nums) + 1) if nums else 1
    name = f"task_{nxt:03d}"
    full = os.path.join(base_dir, name)
    os.makedirs(full, exist_ok=True)
    return full, nxt


def scale_coords(coord):
    x_ai, y_ai = coord
    x_real = int(x_ai * SCREEN_WIDTH / AI_WIDTH)
    y_real = int(y_ai * SCREEN_HEIGHT / AI_HEIGHT)
    return [x_real, y_real]


def take_screenshot(step_dir, step_id):
    screenshot_path = os.path.join(step_dir, f"step_{step_id:02d}.png")
    try:
        img = ImageGrab.grab()
        img.save(screenshot_path, "PNG")
        print(f"Saved screenshot: {screenshot_path}")
    except Exception as e:
        print(f"Failed to save screenshot: {e}")
    return screenshot_path


def run_computer_tool(action, args, step_dir, step_id):
    result = {}
    try:
        if action == "screenshot":
            result["status"] = "manual screenshot taken"

        elif action in ["click", "left_click"]:
            x, y = scale_coords(args.get("coordinate", [0, 0]))
            pyautogui.click(x, y)
            result["status"] = f"clicked at ({x},{y})"

        elif action == "double_click":
            x, y = scale_coords(args.get("coordinate", [0, 0]))
            pyautogui.doubleClick(x, y)
            result["status"] = f"double-clicked at ({x},{y})"

        elif action == "type":
            text = args.get("text", "")
            pyautogui.typewrite(text, interval=0.05)
            result["status"] = f"typed '{text}'"

        elif action == "press":
            key = args.get("key")
            pyautogui.press(key)
            result["status"] = f"pressed key '{key}'"

        elif action == "wait":
            seconds = args.get("seconds", 1)
            time.sleep(seconds)
            result["status"] = f"waited {seconds} seconds"

        else:
            result["error"] = f"Unknown action: {action}"

    except Exception as e:
        result["error"] = f"Failed to run action {action}: {e}"

    result["screenshot"] = take_screenshot(step_dir, step_id)
    return result


def run_bash_tool(command, step_dir, step_id):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = {"stdout": result.stdout, "stderr": result.stderr}
    output["screenshot"] = take_screenshot(step_dir, step_id)
    return output


def run_editor_tool(args, step_dir, step_id):
    result = {"status": "editor action simulated", "args": args}
    result["screenshot"] = take_screenshot(step_dir, step_id)
    return result


def save_step_data(step_dir, step_id, response, tool_output):
    step_data = {
        "response": [block.model_dump() for block in response.content],
        "tool_output": tool_output
    }
    with open(os.path.join(step_dir, f"step_{step_id:02d}.json"), "w") as f:
        json.dump(step_data, f, indent=2)


# -------------------------------
# Main
# -------------------------------
def run_single_task(task_text: str):
    task_dir, task_num = next_task_dir(TRAJECTORY_DIR)
    print(f"\n=== Running Task {task_num:03d}: {task_text} ===")

    # Save task text
    with open(os.path.join(task_dir, f"task_{task_num:03d}.txt"), "w") as f:
        f.write(task_text)

    messages = [{"role": "user", "content": task_text}]
    last_action = None
    repeat_count = 0

    for step in range(1, MAX_STEPS + 1):
        try:
            response = client.beta.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                tools=[
                    {"type": "computer_20250124", "name": "computer",
                     "display_width_px": AI_WIDTH, "display_height_px": AI_HEIGHT,
                     "display_number": 1},
                    {"type": "text_editor_20250124", "name": "str_replace_editor"},
                    {"type": "bash_20250124", "name": "bash"},
                ],
                messages=messages,
                betas=["computer-use-2025-01-24"]
            )
        except Exception as e:
            print(f"Error at Step {step}: {e}")
            return

        messages.append({"role": "assistant", "content": response.content})

        did_tool_use = False
        tool_output = None

        for block in response.content:
            if block.type == "tool_use":
                did_tool_use = True
                tool_name = block.name
                tool_input = block.input

                if tool_input == last_action:
                    repeat_count += 1
                else:
                    repeat_count = 0
                last_action = tool_input

                if repeat_count > MAX_REPEATS:
                    print("Skipping repeated action")
                    continue

                if tool_name == "computer":
                    tool_output = run_computer_tool(tool_input.get("action"), tool_input, task_dir, step)
                elif tool_name == "bash":
                    tool_output = run_bash_tool(tool_input.get("command", ""), task_dir, step)
                elif tool_name == "str_replace_editor":
                    tool_output = run_editor_tool(tool_input, task_dir, step)
                else:
                    tool_output = {"error": f"Unknown tool: {tool_name}"}

                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": [{"type": "text", "text": f"Result: {tool_output}"}]
                    }]
                })

                save_step_data(task_dir, step, response, tool_output)

        if not did_tool_use:
            print(f"Task {task_num:03d} DONE in {step} steps.")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run one Anthropic macOS GUI task.")
    # single positional argument: the task description
    parser.add_argument("task", type=str, help="Task description to execute (quoted if it contains spaces).")
    args = parser.parse_args()
    run_single_task(args.task)
