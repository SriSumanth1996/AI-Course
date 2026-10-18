from __future__ import annotations

import json
import re
import time
from html import escape

import streamlit as st

from services.openai_chat import stream_tokens

MODEL = "gpt-4o-mini"
COT_MODEL = "gpt-4.1"
TEMPERATURES = {"zero": 1.3, "one": 0.7, "few": 0.0}
LABELS = {
    "zero": "Zero-shot",
    "one": "One-shot",
    "few": "Few-shot",
}
LEADS = {
    "zero": "This prompt has no example. Green fields match the expected answer. Red fields do not.",
    "one": "This prompt has one example. Green fields match the expected answer. Red fields do not.",
    "few": "This prompt has three examples. Green fields match the expected answer. Red fields do not.",
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
        "<p class='prompt-kicker'>Prompt</p>"
        f"<pre class='prompt-source'>{escape(PROMPT_BODIES[shot])}</pre>"
        "</section>"
        "<section class='prompt-block'>"
        "<p class='prompt-kicker'>Review</p>"
        f"<p class='prompt-review'>{escape(NOTE)}</p>"
        "</section>"
        "<section class='prompt-block'>"
        "<p class='prompt-kicker'>Answer</p>"
        f"{answer_html}"
        "</section>"
        "</article>"
    )


CART_PROBLEM = """Problem: Find the Cheapest Shopping Strategy

A customer wants to buy three products:

| Product | Price |
| --- | --- |
| A | ₹1,800 |
| B | ₹1,200 |
| C | ₹900 |

Rules:
1. Every order gets a 30% discount, capped at ₹500.
2. Shipping costs ₹120 per order, but is free for orders of ₹2,000 or more.

Question: Should the customer buy everything together or split the products into separate orders to minimize the total cost?"""

COT_INSTRUCTIONS = {
    "Direct": (
        "Solve the shopping problem using the three product prices and rules "
        "provided. Give only the cheapest strategy and the total amount."
    ),
    "Chain of Thought": (
        "Approach the problem systematically, step by step. Consider all "
        "possible outcomes and how the given conditions affect each one. "
        "Think incrementally, taking into account what has already been "
        "established in previous steps. Reason thoroughly, checking for "
        "overlooked alternatives or inconsistencies, and then provide the "
        "final answer."
    ),
}

CART_PROMPTS = {
    mode: f"{CART_PROBLEM}\n\n{text}" for mode, text in COT_INSTRUCTIONS.items()
}

COT_LEAD = (
    "Pick Direct or Chain of Thought, then press Send. The problem stays the same. "
    "The selected prompt is what the model receives."
)


def _approach_model(mode: str) -> str:
    if mode == "Chain of Thought":
        return COT_MODEL
    return MODEL


def _cot_out_key(mode: str) -> str:
    return f"prompting_out::cot::{mode}"


def _cot_controls(mode: str) -> dict[str, float | int]:
    return {"temperature": 0.0, "top_p": 1}


def _cart_problem_html() -> str:
    rows = (
        ("A", "₹1,800"),
        ("B", "₹1,200"),
        ("C", "₹900"),
    )
    body = "".join(
        f"<tr><td>{product}</td><td>{price}</td></tr>" for product, price in rows
    )
    rules = (
        "<li>Every order gets a 30% discount, capped at ₹500.</li>"
        "<li>Shipping costs ₹120 per order, but is free for orders of ₹2,000 or more.</li>"
    )
    return (
        "<article class='prompt-card'>"
        "<h3>Find the Cheapest Shopping Strategy</h3>"
        "<section class='prompt-block'>"
        "<p class='prompt-kicker'>Problem</p>"
        "<div class='prompt-review prompt-cart'>"
        "<p>A customer wants to buy three products:</p>"
        "<table class='prompt-cart-table'><thead><tr><th>Product</th><th>Price</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
        "<p>Rules</p>"
        f"<ol>{rules}</ol>"
        "<p>Should the customer buy everything together or split the products "
        "into separate orders to minimize the total cost?</p>"
        "</div>"
        "</section>"
        "</article>"
    )


def _formatted_answer(text: str) -> str:
    from lectures.lecture_05 import format_message_html

    return (
        "<div class='model-chat-bubble model-chat-bubble--assistant prompt-answer-rich'>"
        f"{format_message_html(text)}"
        "</div>"
    )


def _cot_answer_html(mode: str | None, text: str, *, busy: bool) -> str:
    if mode is None:
        return (
            "<section class='prompt-block'>"
            "<p class='prompt-kicker'>Answer</p>"
            "<p class='prompt-wait'>Pick Direct or Chain of Thought, then press Send.</p>"
            "</section>"
        )
    answer = text.strip()
    if busy and not answer:
        answer_html = "<p class='prompt-wait'>Running…</p>"
    elif answer:
        answer_html = _formatted_answer(answer)
    else:
        answer_html = "<p class='prompt-wait'>Press Send.</p>"
    return (
        "<article class='prompt-card'>"
        "<section class='prompt-block'>"
        "<p class='prompt-kicker'>Prompt</p>"
        f"<pre class='prompt-source'>{escape(COT_INSTRUCTIONS[mode])}</pre>"
        "</section>"
        "<section class='prompt-block'>"
        "<p class='prompt-kicker'>Answer</p>"
        f"{answer_html}"
        "</section>"
        "</article>"
    )


def render_cot(header_html: str) -> None:
    st.html(
        f"<div class='prompt-split-head'>{header_html}"
        f"<p class='prompt-lead'>{escape(COT_LEAD)}</p></div>"
    )
    send = False
    with st.container(key="prompt_pane_cot"):
        st.html(_cart_problem_html())
        with st.container(key="cot_send_row"):
            pick, action = st.columns(2, vertical_alignment="bottom")
            with pick:
                mode = st.selectbox(
                    "Approach",
                    list(COT_INSTRUCTIONS),
                    index=None,
                    placeholder="Pick Direct or Chain of Thought",
                    key="cot_approach_name",
                )
            with action:
                send = st.button(
                    "Send",
                    key="cot_send",
                    type="primary",
                    disabled=mode is None,
                )
        holder = st.empty()
        saved = st.session_state.get(_cot_out_key(mode), "") if mode else ""
        holder.html(_cot_answer_html(mode, saved, busy=False))
    if not send or not mode:
        return
    acc = ""
    last = 0.0
    holder.html(_cot_answer_html(mode, "", busy=True))
    try:
        for token in stream_tokens(
            _approach_model(mode),
            [{"role": "user", "content": CART_PROMPTS[mode]}],
            kind="prompting",
            controls=_cot_controls(mode),
        ):
            acc += token
            now = time.monotonic()
            if last == 0.0 or now - last >= 0.05:
                holder.html(_cot_answer_html(mode, acc, busy=True))
                last = now
    finally:
        st.session_state[_cot_out_key(mode)] = acc
    holder.html(_cot_answer_html(mode, acc, busy=False))
    st.rerun()


def render(header_html: str, shot: str) -> None:
    st.html(
        f"<div class='prompt-split-head'>{header_html}"
        f"<p class='prompt-lead'>{escape(LEADS[shot])}</p></div>"
    )
    clicked = False
    with st.container(key=f"prompt_pane_{shot}"):
        clicked = st.button(
            LABELS[shot],
            key=f"prompt_run_{shot}",
            type="primary",
        )
        holder = st.empty()
        holder.html(_card(shot, st.session_state.get(_out_key(shot), ""), busy=False))
    if not clicked:
        return
    acc = ""
    last = 0.0
    holder.html(_card(shot, "", busy=True))
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
                holder.html(_card(shot, acc, busy=True))
                last = now
    finally:
        st.session_state[_out_key(shot)] = acc
    holder.html(_card(shot, acc, busy=False))
    st.rerun()
