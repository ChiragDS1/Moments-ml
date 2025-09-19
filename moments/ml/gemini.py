import os, json
from pathlib import Path
from PIL import Image
import google.generativeai as genai

# configure Gemini from .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_client = genai.GenerativeModel(MODEL)

ALT_PROMPT = (
  "You are an accessibility assistant. Write a concise, objective ALT text for screen readers. "
  "Max 160 characters. No extra commentary, no emojis, no brand guessing."
)

TAGS_PROMPT = (
  "List 3-10 salient objects in this photo that would help with search. "
  "Return ONLY JSON with this schema: {\"objects\": [\"noun\", ...]}. "
  "Use lowercase, singular nouns, no duplicates."
)

def _open_image(path: str | Path):
    return Image.open(path)

def generate_alt_text(image_path: str | Path) -> str | None:
    img = _open_image(image_path)
    resp = _client.generate_content([ALT_PROMPT, img])
    text = (resp.text or "").strip()
    return text[:160] if text else None

def generate_objects(image_path: str | Path) -> list[str]:
    img = _open_image(image_path)
    resp = _client.generate_content(
        [TAGS_PROMPT, img],
        generation_config={"response_mime_type": "application/json"}
    )
    try:
        data = json.loads(resp.text or "{}")
        objects = data.get("objects", [])
        clean = sorted({o.strip().lower() for o in objects if isinstance(o, str) and o.strip()})
        return clean[:12]
    except Exception:
        return []
