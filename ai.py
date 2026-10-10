import os
from google import genai
from google.genai import types

from personality import SYSTEM_PROMPT

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


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
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=1.1,
            max_output_tokens=180,
        ),
    )

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response")

    return text
