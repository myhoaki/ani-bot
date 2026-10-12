from google import genai
from google.genai import types

from core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_MAX_OUTPUT_TOKENS,
)
from core.personality import SYSTEM_PROMPT

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_reply(history: list[dict[str, str]], instruction: str) -> str:
    """Generate one short Discord-style Ani reply."""
    contents = []

    for message in history:
        contents.append(
            types.Content(
                role=message["role"],
                parts=[types.Part(text=message["text"])],
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=instruction)],
        )
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=GEMINI_TEMPERATURE,
            max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
        ),
    )

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response")

    return text
