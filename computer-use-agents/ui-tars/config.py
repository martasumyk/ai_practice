import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY") and os.getenv("HF_TOKEN"):
    os.environ["OPENAI_API_KEY"] = os.getenv("HF_TOKEN")

HF_BASE_URL = os.getenv("HF_BASE_URL")
HF_TOKEN    = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
MODEL_ID    = os.getenv("MODEL_ID", "ByteDance-Seed/UI-TARS-1.5-7B")

LOG_ROOT    = "sessions"

TASK        = "Open System Settings and enable Night Shift."

PROMPT_TEMPLATE = """You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format
Thought: ...
Action: ...

## Action Space
click(point='<point>x1 y1</point>')
left_double(point='<point>x1 y1</point>')
right_single(point='<point>x1 y1</point>')
drag(start_point='<point>x1 y1</point>', end_point='<point>x2 y2</point>')
hotkey(key='ctrl c')
type(content='xxx')
scroll(point='<point>x1 y1</point>', direction='down or up or right or left')
wait()
finished(content='xxx')

## Note
- Use English in `Thought` part.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in `Thought` part.
- You are controlling a macOS desktop. 

## User Instruction
{instruction}
"""

def build_instruction(task: str) -> str:
    """Return final prompt text for the model for this task."""
    return PROMPT_TEMPLATE.format(instruction=task)
