import io
import os
import base64
import re
import mss
from PIL import Image

def capture_screenshot() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
    return img

def encode_png_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return "data:image/png;base64," + b64

def save_and_encode(step_idx: int, session_dir: str) -> tuple[str, str]:
    os.makedirs(session_dir, exist_ok=True)

    img = capture_screenshot()

    filename = f"step_{step_idx:03d}.png"
    path = os.path.join(session_dir, filename)

    img.save(path, format="PNG")

    data_url = encode_png_b64(img)
    return data_url, path

def add_box_token(text: str) -> str:
    if "Action:" in text and "start_box=" in text:
        prefix = text.split("Action: ")[0] + "Action: "
        actions = text.split("Action: ")[1:]
        out_parts = []

        for a in actions:
            a = a.strip()
            coords = re.findall(r"(start_box|end_box)='\((\d+),\s*(\d+)\)'", a)
            upd = a

            for coord_type, x, y in coords:
                old = f"{coord_type}='({x},{y})'"
                new = f"{coord_type}='<|box_start|>({x},{y})<|box_end|>'"
                upd = upd.replace(old, new)

            out_parts.append(upd)

        return prefix + "\n\n".join(out_parts)

    return text
