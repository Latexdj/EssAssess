"""
Thin wrapper around the Google Gemini API.
Free tier: gemini-1.5-flash — 1,500 req/day, 1M tokens/min.
Returns the same dict shape as call_claude so ports.py can swap transparently.
"""
import google.generativeai as genai

from app.config import settings

GRADING_MODEL = "gemini-1.5-flash"
MAX_TOKENS    = 2048


async def call_gemini(
    system:           str,
    user:             str,
    image_base64:     str | None = None,
    image_media_type: str = "image/jpeg",
) -> dict:
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(
        model_name=GRADING_MODEL,
        system_instruction=system,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=0.0,
        ),
    )

    parts: list = []
    if image_base64:
        parts.append({
            "inline_data": {
                "mime_type": image_media_type,
                "data":      image_base64,
            }
        })
    parts.append(user)

    response = await model.generate_content_async(parts)

    return {
        "text":          response.text,
        "model":         GRADING_MODEL,
        "input_tokens":  response.usage_metadata.prompt_token_count,
        "output_tokens": response.usage_metadata.candidates_token_count,
    }
