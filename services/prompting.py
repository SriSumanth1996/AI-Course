from __future__ import annotations

import json
import re
import time
from html import escape

import streamlit as st

from services.openai_chat import stream_tokens

TOPIC = "Shop note"
MODEL = "gpt-4o-mini"
TEMPERATURES = {"zero": 1.3, "one": 0.7, "few": 0.0}
SHOTS = ("zero", "one", "few")
LABELS = {
    "zero": "Zero-shot",
    "one": "One-shot",
    "few": "Few-shot",
}

NOTE = (
    "Order 4418. The packing note said two boxes. The cups I purchased are "
    "excellent and arrived on Friday, but the kettle I bought last week will "
    "not switch on, even after trying another socket. I emailed support that "
    "Friday. I am travelling on Monday, and the hotel has no kettle. Please "
    "replace the kettle before I leave. If a replacement is impossible, a "
    "refund is acceptable. I do not want a repair, and do not touch the cups."
)

INSTRUCTION = (
    "Turn the following shop note into one JSON object. "
    "Return only that JSON object."
)

PRAISE = """Example: These headphones sound wonderful.
{"intent": "Praise", "item": "Headphones", "issue": "None", "urgency": "Low", "primary_action": "None", "fallback_action": "None", "deadline": "None"}"""

QUESTION = """Example: Does this suitcase fit overhead? I fly Thursday.
{"intent": "Question", "item": "Suitcase", "issue": "None", "urgency": "Low", "primary_action": "Information", "fallback_action": "None", "deadline": "Thursday"}"""

COMPLAINT = """Example: The lamp is lovely, but the toaster will not stay down. Wrote Saturday. Picnic Sunday. New toaster before Sunday, else refund. Do not repair it. Leave the lamp.
{"intent": "Complaint", "item": "Toaster", "issue": "Will not stay down", "urgency": "High", "primary_action": "Replacement", "fallback_action": "Refund", "deadline": "Sunday"}"""

EXPECTED = {
    "intent": "Complaint",
    "item": "Kettle",
    "issue": "Will not switch on",
    "urgency": "High",
    "primary_action": "Replacement",
    "fallback_action": "Refund",
    "deadline": "Monday",
}

PROMPT_BODIES = {
    "zero": INSTRUCTION,
    "one": f"{INSTRUCTION}\n\n{PRAISE}",
    "few": f"{INSTRUCTION}\n\n{PRAISE}\n\n{QUESTION}\n\n{COMPLAINT}",
}

PROMPTS = {
    shot: f"{body}\n\nNote: {NOTE}" for shot, body in PROMPT_BODIES.items()
}


def _out_key(shot: str) -> str:
    return f"prompting_out::{shot}"


def _controls(shot: str) -> dict[str, float | int]:
    return {"temperature": TEMPERATURES[shot], "top_p": 1, "max_tokens": 400}


def _json_object(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _fields_html(text: str) -> str:
    parsed = _json_object(text)
    rows = [
        "<div class='prompt-field prompt-field--head'>"
        "<span class='prompt-field-key'>Field</span>"
        "<span class='prompt-field-got'>Answer</span>"
        "<span class='prompt-field-exp'>Expected</span>"
        "</div>"
    ]
    for key, expected in EXPECTED.items():
        got = ""
        if parsed is not None and key in parsed and parsed[key] is not None:
            got = str(parsed[key])
        hit = parsed is not None and got == expected
        mark = "is-match" if hit else "is-miss"
        shown = got if got else "—"
        rows.append(
            "<div class='prompt-field %s'>"
            "<span class='prompt-field-key'>%s</span>"
            "<span class='prompt-field-got'>%s</span>"
            "<span class='prompt-field-exp'>%s</span>"
            "</div>"
            % (mark, escape(key), escape(shown), escape(expected))
        )
    return "<div class='prompt-fields'>%s</div>" % "".join(rows)


def _card(shot: str, text: str, *, busy: bool) -> str:
    answer = escape(text.strip()) if text.strip() else ""
    if busy and not answer:
        answer_html = "<p class='prompt-wait'>Running…</p>"
    elif answer:
        answer_html = f"<pre class='prompt-answer'>{answer}</pre>{_fields_html(text)}"
    else:
        answer_html = "<p class='prompt-wait'>Run this pane to see the JSON.</p>"
    return (
        "<article class='prompt-card'>"
        f"<h3>{escape(LABELS[shot])}</h3>"
        "<section class='prompt-block'>"
        "<p class='prompt-kicker'>Review</p>"
        f"<p class='prompt-review'>{escape(NOTE)}</p>"
        "</section>"
        "<section class='prompt-block'>"
        "<p class='prompt-kicker'>Prompt</p>"
        f"<pre class='prompt-source'>{escape(PROMPT_BODIES[shot])}</pre>"
        "</section>"
        "<section class='prompt-block'>"
        "<p class='prompt-kicker'>Answer</p>"
        f"{answer_html}"
        "</section>"
        "</article>"
    )


def render(header_html: str) -> None:
    st.html(
        f"<div class='prompt-split-head'>{header_html}"
        "<p class='prompt-lead'>Each pane starts with the same review, then the prompt. "
        "Zero-shot has no example. One-shot has one. Few-shot has three. "
        "Green fields match the expected answer. Red fields do not.</p></div>"
    )
    clicked: dict[str, bool] = {}
    with st.container(key="prompt_split", horizontal=True, wrap=False, gap="small"):
        holders = {}
        for shot in SHOTS:
            with st.container(key=f"prompt_pane_{shot}"):
                clicked[shot] = st.button(
                    LABELS[shot],
                    key=f"prompt_run_{shot}",
                    type="primary",
                )
                holders[shot] = st.empty()
                holders[shot].html(
                    _card(shot, st.session_state.get(_out_key(shot), ""), busy=False)
                )
    for shot in SHOTS:
        if not clicked[shot]:
            continue
        acc = ""
        last = 0.0
        holders[shot].html(_card(shot, "", busy=True))
        try:
            for token in stream_tokens(
                MODEL,
                [{"role": "user", "content": PROMPTS[shot]}],
                kind="prompting",
                controls=_controls(shot),
            ):
                acc += token
                now = time.monotonic()
                if last == 0.0 or now - last >= 0.05:
                    holders[shot].html(_card(shot, acc, busy=True))
                    last = now
        finally:
            st.session_state[_out_key(shot)] = acc
        holders[shot].html(_card(shot, acc, busy=False))
        st.rerun()
