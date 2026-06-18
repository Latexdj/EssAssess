"""
Thin wrapper around the Google Gemini API (google-genai SDK).
Free tier: gemini-2.0-flash — generous daily limits for testing.
Returns the same dict shape as call_claude so ports.py can swap transparently.
"""
import base64
from google import genai
from google.genai import types

from app.config import settings

GRADING_MODEL = "gemini-2.0-flash"
MAX_TOKENS    = 2048


async def call_gemini(
    system:           str,
    user:             str,
    image_base64:     str | None = None,
    image_media_type: str = "image/jpeg",
) -> dict:
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    client = genai.Client(api_key=settings.google_api_key)

    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=image_media_type),
            types.Part.from_text(text=user),
        ]
    else:
        contents = user  # plain string works for text-only requests

    response = await client.aio.models.generate_content(
        model=GRADING_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=MAX_TOKENS,
            temperature=0.0,
        ),
    )

    usage = response.usage_metadata
    return {
        "text":          response.text,
        "model":         GRADING_MODEL,
        "input_tokens":  usage.prompt_token_count if usage else 0,
        "output_tokens": usage.candidates_token_count if usage else 0,
    }
