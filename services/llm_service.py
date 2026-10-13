
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PROMPT_PATH = _PROJECT_ROOT / "prompts" / "qa_review_prompt.txt"
_MODEL_NAME = "gemini-3-flash-preview"


def analyze_requirement(requirement: str) -> str:
    if not requirement or not str(requirement).strip():
        raise ValueError("Requirement text is empty.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Set it in the environment or in a .env file."
        )

    if not _PROMPT_PATH.is_file():
        raise FileNotFoundError(
            f"Prompt file not found: {_PROMPT_PATH}"
        )

    prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.replace(
        "{requirement}", str(requirement).strip()
    )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_MODEL_NAME)
        response = model.generate_content(prompt)

    except Exception as exc:
        print(f"Gemini diagnostic: {type(exc).__name__}: {exc}")
        raise RuntimeError(
            "Gemini analysis failed. Check the terminal for details."
        ) from exc

    text = getattr(response, "text", None)

    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("Gemini returned an empty response.")

    return text.strip()
