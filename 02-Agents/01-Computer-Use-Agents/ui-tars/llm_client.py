from typing import List, Dict
from openai import OpenAI
from config import HF_BASE_URL, MODEL_ID, build_instruction
import os

def init_client() -> OpenAI:
    return OpenAI(
        base_url=HF_BASE_URL,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

def build_messages(task: str,
                   history: List[Dict[str, str]],
                   screenshot_b64: str) -> list[dict]:
    user_turn = {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": screenshot_b64}
            },
            {
                "type": "text",
                "text": build_instruction(task)
            }
        ]
    }

    # current user turn first, then previous assistant turns
    msgs = [user_turn] + history
    return msgs

def query_model(client: OpenAI, messages: list[dict]) -> str:
    """
    Call the model and return the assistant text ("Thought... Action: ...").
    """
    completion = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        temperature=0.0,
        max_tokens=400,
        stream=False
    )
    return completion.choices[0].message.content
