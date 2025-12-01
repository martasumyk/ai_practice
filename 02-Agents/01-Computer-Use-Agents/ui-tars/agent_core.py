import os
import re
import time
import json
import pyautogui
from datetime import datetime
from typing import Dict, List, Any

from vision import save_and_encode, add_box_token
from llm_client import build_messages, query_model, init_client
from config import TASK, LOG_ROOT


def extract_thought(model_reply: str) -> str:
    m = re.search(r"Thought:\s*(.*?)(?:\nAction:|\Z)", model_reply, flags=re.DOTALL)

    if not m:
        return ""

    return m.group(1).strip()


def parse_action_block(model_reply: str) -> Dict[str, Any]:

    m = re.search(r"Action:\s*(.+)", model_reply)
    if not m:
        return {"type": "none"}
    action_str = m.group(1).strip()

    # finished(content='...')
    m_fin = re.match(r"finished\(content='(.*)'\)", action_str)
    if m_fin:
        return {"type": "finished", "content": m_fin.group(1)}

    # click(start_box=... or end_box=...)
    m_click_box = re.match(
        r"click\((start_box|end_box)='.*?\((\d+)\s*,\s*(\d+)\).*?'\)",
        action_str
    )
    if m_click_box:
        x = int(m_click_box.group(2))
        y = int(m_click_box.group(3))
        return {
            "type": "click",
            "x": x,
            "y": y,
        }

    # click / left_double / right_single with <point>x y</point>
    m_click = re.match(
        r"(click|left_double|right_single)\(point='<point>(\d+)\s+(\d+)</point>'\)",
        action_str
    )
    if m_click:
        return {
            "type": m_click.group(1),
            "x": int(m_click.group(2)),
            "y": int(m_click.group(3)),
        }

    # drag(start_point=..., end_point=...)
    m_drag = re.match(
        r"drag\(start_point='<point>(\d+)\s+(\d+)</point>',\s*end_point='<point>(\d+)\s+(\d+)</point>'\)",
        action_str
    )
    if m_drag:
        return {
            "type": "drag",
            "x1": int(m_drag.group(1)),
            "y1": int(m_drag.group(2)),
            "x2": int(m_drag.group(3)),
            "y2": int(m_drag.group(4)),
        }

    # hotkey(key='ctrl c')
    m_hotkey = re.match(r"hotkey\(key='([^']+)'\)", action_str)
    if m_hotkey:
        keys = m_hotkey.group(1).split()
        return {"type": "hotkey", "keys": keys}

    # type(content='hello\\n')
    m_type = re.match(r"type\(content='(.*)'\)", action_str)
    if m_type:
        txt = m_type.group(1)
        txt = txt.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
        return {"type": "type", "text": txt}

    # scroll(point='<point>x y</point>', direction='down')
    m_scroll = re.match(
        r"scroll\(point='<point>(\d+)\s+(\d+)</point>',\s*direction='(down|up|left|right)'\)",
        action_str
    )
    if m_scroll:
        return {
            "type": "scroll",
            "x": int(m_scroll.group(1)),
            "y": int(m_scroll.group(2)),
            "direction": m_scroll.group(3),
        }

    # wait()
    if re.match(r"wait\(\)", action_str):
        return {"type": "wait"}

    return {"type": "raw", "raw": action_str}


def execute_action(a: Dict[str, Any]) -> str | None:
    t = a["type"]

    if t in ["click", "left_double", "right_single"]:
        x, y = a["x"], a["y"]
        pyautogui.moveTo(x, y, duration=0.15)
        if t == "click":
            pyautogui.click()
        elif t == "left_double":
            pyautogui.doubleClick()
        elif t == "right_single":
            pyautogui.click(button="right")

    elif t == "drag":
        pyautogui.moveTo(a["x1"], a["y1"], duration=0.15)
        pyautogui.dragTo(a["x2"], a["y2"], duration=0.3, button="left")

    elif t == "hotkey":
        pyautogui.hotkey(*a["keys"])

    elif t == "type":
        pyautogui.typewrite(a["text"], interval=0.02)

    elif t == "scroll":
        pyautogui.moveTo(a["x"], a["y"], duration=0.1)
        if a["direction"] == "down":
            pyautogui.scroll(-500)
        elif a["direction"] == "up":
            pyautogui.scroll(500)

    elif t == "wait":
        time.sleep(5)

    elif t == "finished":
        print("[Agent finished]:", a.get("content", ""))
        return "FINISHED"

    else:
        print("[Unhandled action]:", a)

    return None


def make_session_dir() -> str:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    session_dir = os.path.join(LOG_ROOT, ts)
    os.makedirs(session_dir, exist_ok=True)

    return session_dir


def run_agent(task: str, max_steps: int = 15, safety_max_steps: int | None = None):
    """
    - take screenshot
    - send screenshot+history to model
    - save screenshot and all metadata
    - execute action
    - repeat
    """

    client = init_client()
    history: List[dict] = [] 
    step_logs: List[dict] = [] 

    session_dir = make_session_dir()

    for step in range(max_steps):
        if safety_max_steps is not None and step >= safety_max_steps:
            print("Safety stop reached.")
            break

        screenshot_b64, screenshot_path = save_and_encode(step, session_dir)

        msgs = build_messages(task, history, screenshot_b64)

        raw_reply = query_model(client, msgs)

        reply = add_box_token(raw_reply)

        action = parse_action_block(reply)
        thought = extract_thought(reply)

        print(f"\nStep {step}")
        print(reply)

        status = execute_action(action)

        step_logs.append({
            "step": step,
            "screenshot_path": screenshot_path,
            "model_reply": reply,
            "thought": thought,
            "parsed_action": action,
            "status_after_action": status,
        })

        history.append({
            "role": "assistant",
            "content": reply
        })

        if status == "FINISHED":
            break

        time.sleep(1)

    session_log_path = os.path.join(session_dir, "session_log.json")
    with open(session_log_path, "w") as f:
        json.dump(
            {
                "task": task,
                "steps": step_logs,
            },
            f,
            indent=2
        )

    print(f"\nSession data saved in {session_dir}")


def run_default_agent():
    run_agent(TASK, max_steps=10, safety_max_steps=5)
