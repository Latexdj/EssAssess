"""
Thin wrapper around the Anthropic API.
Handles text-only and image+text (vision) grading requests.
"""
import anthropic

from app.config import settings

GRADING_MODEL  = "claude-sonnet-4-5"
MAX_TOKENS     = 2048
TEMPERATURE    = 0        # deterministic for reproducible grading


async def call_claude(
    system:          str,
    user:            str,
    image_base64:    str | None = None,
    image_media_type: str = "image/jpeg",
) -> dict:
    """
    Call Claude and return a dict with:
      text, model, input_tokens, output_tokens
    Raises anthropic.APIError on API failure (caller should handle).
    """
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Build the user message content
    content: list[dict] = []
    if image_base64:
        content.append({
            "type":   "image",
            "source": {
                "type":       "base64",
                "media_type": image_media_type,
                "data":       image_base64,
            },
        })
    content.append({"type": "text", "text": user})

    response = await client.messages.create(
        model=GRADING_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system,
        messages=[{"role": "user", "content": content}],
    )

    return {
        "text":          response.content[0].text,
        "model":         response.model,
        "input_tokens":  response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
