from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from services.keys import openai_api_key
from services.prompts import llm_messages

MISSING_KEY = (
    "OpenAI API key was not found. For offline use, put it in openAI API.txt. "
    "On Streamlit Cloud, add OPENAI_API_KEY in Secrets."
)


def build_request(
    model_id: str,
    messages: list[dict[str, str]],
    *,
    document: str = "",
    controls: dict[str, object] | None = None,
) -> dict[str, object]:
    request: dict[str, object] = {
        "model": model_id,
        "messages": llm_messages(messages, document),
        "stream": True,
    }
    if controls:
        request.update(controls)
    return request


def chat(
    model_id: str,
    messages: list[dict[str, str]],
    *,
    document: str = "",
    controls: dict[str, object] | None = None,
) -> str:
    return "".join(
        stream_tokens(
            model_id,
            messages,
            document=document,
            controls=controls,
        )
    )


def stream_tokens(
    model_id: str,
    messages: list[dict[str, str]],
    *,
    document: str = "",
    controls: dict[str, object] | None = None,
) -> Iterator[str]:
    key = openai_api_key()
    if not key:
        yield MISSING_KEY
        return

    request = build_request(
        model_id,
        messages,
        document=document,
        controls=controls,
    )

    try:
        stream = OpenAI(api_key=key).chat.completions.create(**request)
        for event in stream:
            if not event.choices:
                continue
            piece = event.choices[0].delta.content
            if piece:
                yield piece
    except Exception as exc:
        yield f"OpenAI could not answer with {model_id}: {exc}"
