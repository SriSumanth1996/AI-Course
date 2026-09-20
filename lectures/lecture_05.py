from __future__ import annotations

import json
import re
import time
from base64 import b64encode
from html import escape
from pathlib import Path

import streamlit as st

from services.documents import extract_upload
from services.huggingface_chat import LLAMA_BASE_MODEL
from services.huggingface_chat import LLAMA_INSTRUCT_MODEL
from services.huggingface_chat import chat as llama_chat
from services.huggingface_chat import stream_tokens as llama_stream_tokens
from services.llama_controls import DEFAULT_FREQUENCY_PENALTY
from services.llama_controls import DEFAULT_TEMPERATURE
from services.llama_controls import DEFAULT_TOP_P
from services.llama_controls import clamp_frequency_penalty
from services.llama_controls import clamp_temperature
from services.llama_controls import clamp_top_p
from services.llama_controls import request_params as llama_request_params
from services.openai_chat import chat as openai_chat
from services.openai_chat import stream_tokens as openai_stream_tokens
from services.openai_controls import (
    DEFAULT_OUTPUT_LENGTH,
    DEFAULT_REASONING,
    DEFAULT_VERBOSITY,
    OUTPUT_LENGTH_HINTS,
    OUTPUT_LENGTHS,
    VERBOSITY_OPTIONS,
    request_params,
    spec_for,
    temperature_allowed,
)

openai_stream_words = openai_stream_tokens

TITLE = "Lecture 5"
SUB_LECTURES = ["Tokenisation", "Input context", "Post Training"]
TOPICS = {
    "Post Training": [
        "Base Model",
        "Fine-tuned Model",
        "RLHF-aligned Model",
    ],
}
PICK_SUB = (
    "Pick Tokenisation, Input context, or Post Training to open that section."
)
PICK_TOPIC = (
    "Pick Base Model, Fine-tuned Model, or RLHF-aligned Model to open that section."
)

ASSETS = Path(__file__).resolve().parent.parent / "assets"

RLHF_CATALOG = {
    "OpenAI": {
        "GPT-4o Mini": "gpt-4o-mini",
        "GPT-4.1": "gpt-4.1",
        "GPT-5.2": "gpt-5.2",
        "GPT-5.6 Sol": "gpt-5.6-sol",
    },
    "Anthropic": {
        "Claude Sonnet 4.5": "claude-sonnet-4-5",
        "Claude Haiku 4.5": "claude-haiku-4-5",
        "Claude Opus 4.5": "claude-opus-4-5",
        "Claude Sonnet 4.6": "claude-sonnet-4-6",
        "Claude Opus 4.8": "claude-opus-4-8",
        "Claude Sonnet 5": "claude-sonnet-5",
        "Claude Opus 5": "claude-opus-5",
        "Claude Fable 5": "claude-fable-5",
    },
}

DEFAULT_RLHF_COMPANY = "OpenAI"
DEFAULT_RLHF_MODEL = {
    "OpenAI": "GPT-4o Mini",
    "Anthropic": "Claude Sonnet 4.5",
}

ASSISTANT_MARK = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="#111111" d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/>'
    "</svg>"
)

ALLOWED_UPLOAD_EXTS = {".pdf", ".doc", ".docx", ".txt"}
UPLOAD_FILE_TYPES = ["pdf", "doc", "docx", "txt"]
UPLOAD_REJECT = "Only Word, PDF or text files are accepted."
DOC_PREVIEW_CHARS = 900


TYPING_DOTS = (
    '<span class="chat-wave-dots" aria-label="Generating">'
    "<span>.</span><span>.</span><span>.</span>"
    "</span>"
)


def chat_key(topic: str) -> str:
    return f"chat_messages::{topic}"


def doc_context_key(topic: str) -> str:
    return f"doc_context::{topic}"


COMPANY_LOGOS = {
    "OpenAI": "openai.svg",
    "Anthropic": "anthropic.svg",
    "Meta": "meta.svg",
}

LLAMA_TOPICS = {"Base Model", "Fine-tuned Model"}
LLAMA_SCOPE = {
    "Base Model": "base",
    "Fine-tuned Model": "instruct",
}


def llama_scope(topic: str) -> str:
    return LLAMA_SCOPE[topic]


def llama_key(topic: str, name: str) -> str:
    return f"llama_{llama_scope(topic)}_{name}"


def company_mark(company: str, color: str) -> str:
    svg = (ASSETS / "logos" / COMPANY_LOGOS[company]).read_text(encoding="utf-8")
    svg = svg.replace("<svg", f'<svg fill="{color}"', 1)
    svg = svg.replace("<path d=", f'<path fill="{color}" d=')
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        f'<img class="rlhf-logo" alt="" src="data:image/svg+xml;base64,{encoded}">'
    )


def ensure_rlhf_company() -> str:
    company = st.session_state.get("rlhf_company")
    if company not in RLHF_CATALOG:
        company = DEFAULT_RLHF_COMPANY
        st.session_state.rlhf_company = company
    models = RLHF_CATALOG[company]
    model = st.session_state.get("rlhf_model")
    if model not in models:
        default = DEFAULT_RLHF_MODEL.get(company)
        st.session_state.rlhf_model = default if default in models else None
    return company


def model_widget_id(model_id: str) -> str:
    return model_id.replace(".", "_")


def rlhf_busy() -> bool:
    return bool(st.session_state.get("rlhf_busy"))


def llama_busy(topic: str) -> bool:
    return bool(st.session_state.get(llama_key(topic, "busy")))


def llama_pending(topic: str) -> dict | None:
    pending = st.session_state.get(llama_key(topic, "pending"))
    return pending if isinstance(pending, dict) else None


def set_llama_run(topic: str, *, busy: bool, pending: dict | None = None) -> None:
    st.session_state[llama_key(topic, "busy")] = busy
    st.session_state[llama_key(topic, "pending")] = pending


def request_chat_stop(topic: str) -> None:
    st.session_state.rlhf_pending = None
    st.session_state.rlhf_busy = False
    if topic in LLAMA_TOPICS:
        set_llama_run(topic, busy=False)
    settle_partial_assistant(topic)


def assistant_body_text(content: str) -> str:
    text = (content or "").strip()
    if "This answer is being generated by" in text or text.startswith(
        "This answer is generated by"
    ):
        _, _, rest = text.partition("\n\n")
        return rest.strip()
    return text


def settle_partial_assistant(topic: str) -> None:
    history = st.session_state.get(chat_key(topic), [])
    if not history:
        return
    last = history[-1]
    if last.get("role") != "assistant":
        return
    if last.get("status") not in {"generating", "streaming"}:
        return
    last["content"] = with_rlhf_note(
        topic, assistant_body_text(last.get("content") or ""), done=True
    )
    last["status"] = "done"


def commit_assistant(
    history: list[dict],
    topic: str,
    text: str,
    *,
    company: str | None = None,
) -> None:
    reply = with_rlhf_note(topic, text, done=True)
    if history and history[-1]["role"] == "assistant":
        history[-1]["content"] = reply
        history[-1]["status"] = "done"
        if company:
            history[-1]["company"] = company
        return
    row = {"role": "assistant", "content": reply, "status": "done"}
    if company:
        row["company"] = company
    history.append(row)


def recover_rlhf_lock() -> None:
    if st.session_state.get("rlhf_busy") and not st.session_state.get("rlhf_pending"):
        st.session_state.rlhf_busy = False


def recover_llama_lock(topic: str) -> None:
    if llama_busy(topic) and not llama_pending(topic):
        set_llama_run(topic, busy=False)


def ensure_llama_control_mode(topic: str) -> str:
    mode = st.session_state.get(llama_key(topic, "control_mode"))
    if mode not in {"Auto", "Manual"}:
        mode = "Auto"
        st.session_state[llama_key(topic, "control_mode")] = mode
    return mode


def select_llama_control_mode(topic: str, mode: str) -> None:
    if llama_busy(topic):
        return
    if mode in {"Auto", "Manual"}:
        reset_llama_control_state(topic)
        st.session_state[llama_key(topic, "control_mode")] = mode


def ensure_llama_output_length(topic: str) -> str:
    label = st.session_state.get(llama_key(topic, "output_length"))
    if label not in OUTPUT_LENGTHS:
        label = DEFAULT_OUTPUT_LENGTH
        st.session_state[llama_key(topic, "output_length")] = label
    return label


def _optional_float(key: str, clamp) -> float | None:
    value = st.session_state.get(key)
    if value is None:
        return None
    try:
        return clamp(float(value))
    except (TypeError, ValueError):
        st.session_state[key] = None
        return None


def ensure_llama_temperature(topic: str) -> float | None:
    return _optional_float(llama_key(topic, "temperature"), clamp_temperature)


def ensure_llama_top_p(topic: str) -> float | None:
    return _optional_float(llama_key(topic, "top_p"), clamp_top_p)


def ensure_llama_frequency_penalty(topic: str) -> float | None:
    return _optional_float(llama_key(topic, "frequency_penalty"), clamp_frequency_penalty)


def ensure_llama_controls(topic: str) -> None:
    ensure_llama_output_length(topic)
    ensure_llama_temperature(topic)
    ensure_llama_top_p(topic)
    ensure_llama_frequency_penalty(topic)


def default_llama_controls() -> dict:
    return {
        "control_mode": "Auto",
        "output_length": DEFAULT_OUTPUT_LENGTH,
        "temperature": None,
        "top_p": None,
        "frequency_penalty": None,
    }


def reset_llama_control_state(topic: str) -> None:
    defaults = default_llama_controls()
    st.session_state[llama_key(topic, "control_mode")] = defaults["control_mode"]
    st.session_state[llama_key(topic, "output_length")] = defaults["output_length"]
    st.session_state[llama_key(topic, "temperature")] = defaults["temperature"]
    st.session_state[llama_key(topic, "top_p")] = defaults["top_p"]
    st.session_state[llama_key(topic, "frequency_penalty")] = defaults["frequency_penalty"]
    st.session_state[llama_key(topic, "controls_draft")] = ""
    st.session_state.pop(llama_key(topic, "applied_controls"), None)


def schedule_llama_control_reset(topic: str) -> None:
    st.session_state[llama_key(topic, "control_reset_pending")] = True


def apply_scheduled_llama_control_reset(topic: str) -> bool:
    if not st.session_state.pop(llama_key(topic, "control_reset_pending"), False):
        return False
    reset_llama_control_state(topic)
    return True


def llama_controls_ready_for_request(topic: str) -> bool:
    if ensure_llama_control_mode(topic) != "Manual":
        return True
    applied = st.session_state.get(llama_key(topic, "applied_controls"))
    return isinstance(applied, dict)


def llama_control_snapshot(topic: str) -> dict | None:
    ensure_llama_controls(topic)
    if ensure_llama_control_mode(topic) != "Manual":
        return default_llama_controls()
    applied = st.session_state.get(llama_key(topic, "applied_controls"))
    if not isinstance(applied, dict):
        return None
    return {key: applied.get(key) for key in default_llama_controls()}


def llama_controls_from_pending(pending: dict | None) -> dict[str, object]:
    pending = pending or {}
    return llama_request_params(
        control_mode=pending.get("control_mode"),
        output_length=pending.get("output_length"),
        temperature=pending.get("temperature"),
        top_p=pending.get("top_p"),
        frequency_penalty=pending.get("frequency_penalty"),
    )


def apply_llama_control_draft(topic: str) -> None:
    if llama_busy(topic) or ensure_llama_control_mode(topic) != "Manual":
        return
    ensure_llama_controls(topic)
    raw = (st.session_state.get(llama_key(topic, "controls_draft")) or "").strip()
    data: dict = {}
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return
        if not isinstance(parsed, dict):
            return
        data = parsed

    candidate = data.get("output_length")
    if candidate in (None, ""):
        output_length = ensure_llama_output_length(topic)
    elif candidate not in OUTPUT_LENGTHS:
        return
    else:
        output_length = candidate

    def parse_optional(name: str, clamp) -> float | None:
        candidate = data.get(name)
        if candidate in (None, "", "Auto"):
            return None
        try:
            return clamp(float(candidate))
        except (TypeError, ValueError):
            return None

    temperature = parse_optional("temperature", clamp_temperature)
    if data.get("temperature") not in (None, "", "Auto") and temperature is None:
        return
    top_p = parse_optional("top_p", clamp_top_p)
    if data.get("top_p") not in (None, "", "Auto") and top_p is None:
        return
    frequency_penalty = parse_optional("frequency_penalty", clamp_frequency_penalty)
    if data.get("frequency_penalty") not in (None, "", "Auto") and frequency_penalty is None:
        return

    st.session_state[llama_key(topic, "output_length")] = output_length
    st.session_state[llama_key(topic, "temperature")] = temperature
    st.session_state[llama_key(topic, "top_p")] = top_p
    st.session_state[llama_key(topic, "frequency_penalty")] = frequency_penalty
    st.session_state[llama_key(topic, "applied_controls")] = {
        "control_mode": "Manual",
        "output_length": output_length,
        "temperature": temperature,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
    }


def select_rlhf_company(company: str) -> None:
    if rlhf_busy():
        return
    if st.session_state.get("rlhf_company") != company:
        st.session_state.rlhf_company = company
        models = RLHF_CATALOG.get(company, {})
        default = DEFAULT_RLHF_MODEL.get(company)
        st.session_state.rlhf_model = default if default in models else None
        reset_control_state()
        ensure_controls()


def select_rlhf_model(model: str) -> None:
    if rlhf_busy():
        return
    if st.session_state.get("rlhf_model") != model:
        st.session_state.rlhf_model = model
        reset_control_state()
        ensure_controls()


def current_control_model() -> str | None:
    if st.session_state.get("rlhf_company") != "OpenAI":
        return None
    return st.session_state.get("rlhf_model")


def ensure_output_length() -> str:
    spec = spec_for(current_control_model())
    label = st.session_state.get("rlhf_output_length")
    if spec.disabled or not spec.max_tokens or label not in OUTPUT_LENGTHS:
        label = DEFAULT_OUTPUT_LENGTH
        st.session_state.rlhf_output_length = label
    return label


def ensure_reasoning() -> str:
    spec = spec_for(current_control_model())
    label = st.session_state.get("rlhf_reasoning")
    allowed = spec.reasoning or ()
    if spec.disabled or not allowed or label not in allowed:
        label = DEFAULT_REASONING
        st.session_state.rlhf_reasoning = label
    return label


def ensure_verbosity() -> str:
    spec = spec_for(current_control_model())
    label = st.session_state.get("rlhf_verbosity")
    if spec.disabled or not spec.verbosity or label not in VERBOSITY_OPTIONS:
        label = DEFAULT_VERBOSITY
        st.session_state.rlhf_verbosity = label
    return label


def ensure_temperature() -> float | None:
    spec = spec_for(current_control_model())
    reasoning = st.session_state.get("rlhf_reasoning")
    value = st.session_state.get("rlhf_temperature")
    if not temperature_allowed(spec, reasoning):
        return None
    if value is None:
        return None
    try:
        return min(2.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        st.session_state.rlhf_temperature = None
        return None


def ensure_controls() -> None:
    ensure_output_length()
    ensure_reasoning()
    ensure_verbosity()
    ensure_temperature()


def current_controls() -> dict:
    return {
        "control_mode": st.session_state.get("rlhf_control_mode") or "Auto",
        "output_length": st.session_state.get("rlhf_output_length"),
        "reasoning": st.session_state.get("rlhf_reasoning"),
        "verbosity": st.session_state.get("rlhf_verbosity"),
        "temperature": st.session_state.get("rlhf_temperature"),
    }


def default_controls() -> dict:
    return {
        "control_mode": "Auto",
        "output_length": DEFAULT_OUTPUT_LENGTH,
        "reasoning": DEFAULT_REASONING,
        "verbosity": DEFAULT_VERBOSITY,
        "temperature": None,
    }


def reset_control_state() -> None:
    """Reset one-shot controls before their hidden widget is rendered."""
    defaults = default_controls()
    st.session_state.rlhf_control_mode = defaults["control_mode"]
    st.session_state.rlhf_output_length = defaults["output_length"]
    st.session_state.rlhf_reasoning = defaults["reasoning"]
    st.session_state.rlhf_verbosity = defaults["verbosity"]
    st.session_state.rlhf_temperature = defaults["temperature"]
    st.session_state.rlhf_controls_draft = ""
    st.session_state.pop("rlhf_applied_controls", None)
    st.session_state.pop("rlhf_sticky_controls", None)


def schedule_control_reset() -> None:
    # The draft is widget-backed, so it must be cleared on the next rerun,
    # before render_rlhf_buttons() instantiates that widget again.
    st.session_state.rlhf_control_reset_pending = True


def apply_scheduled_control_reset() -> bool:
    if not st.session_state.pop("rlhf_control_reset_pending", False):
        return False
    reset_control_state()
    return True


def ensure_control_mode() -> str:
    mode = st.session_state.get("rlhf_control_mode")
    if mode not in {"Auto", "Manual"}:
        mode = "Auto"
        st.session_state.rlhf_control_mode = mode
    return mode


def select_control_mode(mode: str) -> None:
    if rlhf_busy():
        return
    if mode in {"Auto", "Manual"}:
        reset_control_state()
        st.session_state.rlhf_control_mode = mode


def controls_ready_for_request() -> bool:
    if st.session_state.get("rlhf_company") != "OpenAI":
        return True
    if ensure_control_mode() != "Manual":
        return True
    applied = st.session_state.get("rlhf_applied_controls")
    return (
        isinstance(applied, dict)
        and applied.get("company") == st.session_state.get("rlhf_company")
        and applied.get("model") == st.session_state.get("rlhf_model")
    )


def control_snapshot() -> dict | None:
    ensure_controls()
    if st.session_state.get("rlhf_company") != "OpenAI":
        return default_controls()
    if ensure_control_mode() != "Manual":
        return default_controls()
    applied = st.session_state.get("rlhf_applied_controls")
    if not isinstance(applied, dict):
        return None
    if applied.get("company") != st.session_state.get("rlhf_company"):
        return None
    if applied.get("model") != st.session_state.get("rlhf_model"):
        return None
    return {
        key: applied.get(key)
        for key in default_controls()
    }


def controls_from_pending(pending: dict | None, model: str | None) -> dict[str, object]:
    pending = pending or {}
    if pending.get("control_mode", "Auto") != "Manual":
        return {}
    return request_params(
        model,
        output_length=pending.get("output_length"),
        reasoning=pending.get("reasoning"),
        verbosity=pending.get("verbosity"),
        temperature=pending.get("temperature"),
    )


def apply_control_draft() -> None:
    if rlhf_busy() or ensure_control_mode() != "Manual":
        return
    spec = spec_for(current_control_model())
    if spec.disabled:
        return
    ensure_controls()
    raw = (st.session_state.get("rlhf_controls_draft") or "").strip()
    data: dict = {}
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return
        if not isinstance(parsed, dict):
            return
        data = parsed

    output_length = DEFAULT_OUTPUT_LENGTH
    if spec.max_tokens:
        candidate = data.get("output_length")
        if candidate in (None, ""):
            output_length = ensure_output_length()
        elif candidate not in OUTPUT_LENGTHS:
            return
        else:
            output_length = candidate

    reasoning = DEFAULT_REASONING
    if spec.reasoning:
        candidate = data.get("reasoning")
        if candidate in (None, ""):
            reasoning = ensure_reasoning()
        elif candidate not in spec.reasoning:
            return
        else:
            reasoning = candidate

    verbosity = DEFAULT_VERBOSITY
    if spec.verbosity:
        candidate = data.get("verbosity")
        if candidate in (None, ""):
            verbosity = ensure_verbosity()
        elif candidate not in VERBOSITY_OPTIONS:
            return
        else:
            verbosity = candidate

    temperature = None
    if temperature_allowed(spec, reasoning):
        candidate = data.get("temperature")
        if candidate in (None, "", "Auto"):
            temperature = ensure_temperature()
        else:
            try:
                temperature = min(2.0, max(0.0, float(candidate)))
            except (TypeError, ValueError):
                return

    st.session_state.rlhf_output_length = output_length
    st.session_state.rlhf_reasoning = reasoning
    st.session_state.rlhf_verbosity = verbosity
    st.session_state.rlhf_temperature = temperature
    st.session_state.rlhf_applied_controls = {
        "company": st.session_state.get("rlhf_company"),
        "model": st.session_state.get("rlhf_model"),
        "control_mode": "Manual",
        "output_length": output_length,
        "reasoning": reasoning,
        "verbosity": verbosity,
        "temperature": temperature,
    }


def clear_rlhf_chat() -> None:
    if rlhf_busy():
        return
    st.session_state[chat_key("RLHF-aligned Model")] = []
    st.session_state[doc_context_key("RLHF-aligned Model")] = ""


def clear_llama_chat(topic: str) -> None:
    if llama_busy(topic):
        return
    st.session_state[chat_key(topic)] = []
    st.session_state[doc_context_key(topic)] = ""


def rlhf_ready() -> bool:
    company = st.session_state.get("rlhf_company")
    model = st.session_state.get("rlhf_model")
    return bool(company and model and model in RLHF_CATALOG.get(company, {}))


def rlhf_note(*, done: bool = False) -> str:
    company = st.session_state.get("rlhf_company")
    model = st.session_state.get("rlhf_model")
    if not (company and model and model in RLHF_CATALOG.get(company, {})):
        return ""
    if done:
        return f"This answer is generated by {company}'s {model} from {company}."
    return (
        f"This answer is being generated by {company}'s {model} from {company}."
    )


def llama_note(topic: str, *, done: bool = False) -> str:
    if topic == "Base Model":
        label = "Meta's Llama 3.1 8B base"
    elif topic == "Fine-tuned Model":
        label = "Meta's Llama 3.1 8B Instruct"
    else:
        return ""
    if done:
        return f"This answer is generated by {label}."
    return f"This answer is being generated by {label}."


def with_rlhf_note(topic: str, text: str, *, done: bool = False) -> str:
    if topic in LLAMA_TOPICS:
        note = llama_note(topic, done=done)
    elif topic == "RLHF-aligned Model":
        note = rlhf_note(done=done)
    else:
        return text
    if not note:
        return text
    if not text:
        return note
    return f"{note}\n\n{text}"


def api_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for message in messages:
        role = message.get("role")
        content = (message.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        if "This answer is being generated by" in content:
            continue
        if message.get("status") in {"generating", "streaming"}:
            continue
        if content.startswith("This answer is generated by"):
            _, _, rest = content.partition("\n\n")
            content = rest.strip()
            if not content:
                continue
        history.append({"role": role, "content": content})
    return history


def model_reply(
    topic: str,
    messages: list[dict[str, str]],
    *,
    company: str | None = None,
    model: str | None = None,
    output_length: str | None = None,
    reasoning: str | None = None,
    verbosity: str | None = None,
    temperature: float | None = None,
    control_mode: str | None = None,
) -> str:
    document = st.session_state.get(doc_context_key(topic), "")
    if topic == "Base Model":
        return llama_chat(
            LLAMA_BASE_MODEL,
            api_messages(messages),
            document=document,
            kind="base",
            topic=topic,
        )
    if topic == "Fine-tuned Model":
        return llama_chat(
            LLAMA_INSTRUCT_MODEL,
            api_messages(messages),
            document=document,
            kind="instruct",
            topic=topic,
        )
    if topic == "RLHF-aligned Model":
        company = company or st.session_state.get("rlhf_company")
        model = model or st.session_state.get("rlhf_model")
        models = RLHF_CATALOG.get(company or "", {})
        if not (company and model and model in models):
            return "Select a company and model above, then ask a question."
        if company == "OpenAI":
            extras = (
                request_params(
                    model,
                    output_length=output_length,
                    reasoning=reasoning,
                    verbosity=verbosity,
                    temperature=temperature,
                )
                if (control_mode or ensure_control_mode()) == "Manual"
                else {}
            )
            return openai_chat(
                models[model],
                api_messages(messages),
                document=document,
                controls=extras,
            )
        return (
            f"{model} will answer here once the {company} API is connected."
        )
    return f"{topic} will answer here once its API is connected."


def uploaded_ext(uploaded) -> str:
    return Path(getattr(uploaded, "name", "")).suffix.lower()


def split_uploads(files: list) -> tuple[list, list]:
    accepted: list = []
    rejected: list = []
    for uploaded in files:
        if uploaded_ext(uploaded) in ALLOWED_UPLOAD_EXTS:
            accepted.append(uploaded)
        else:
            rejected.append(uploaded)
    return accepted, rejected


def _preview(content: str) -> str:
    stripped = content.strip()
    if len(stripped) <= DOC_PREVIEW_CHARS:
        return stripped
    return stripped[:DOC_PREVIEW_CHARS].rstrip() + "\n\n…"


def ingest_uploads(topic: str, files: list) -> str:
    stored: list[str] = []
    notes: list[str] = []
    for uploaded in files:
        name = getattr(uploaded, "name", "file")
        try:
            content = extract_upload(uploaded).strip()
        except Exception as exc:
            notes.append(f"Could not read {name}: {exc}")
            continue
        if not content:
            notes.append(f"{name} had no extractable text.")
            continue
        stored.append(f"# {name}\n\n{content}")
        notes.append(
            f"Read {name} as Markdown ({len(content)} characters).\n\n{_preview(content)}"
        )
    if stored:
        key = doc_context_key(topic)
        previous = st.session_state.get(key, "").strip()
        combined = "\n\n---\n\n".join(stored)
        st.session_state[key] = (
            f"{previous}\n\n---\n\n{combined}" if previous else combined
        )
    return (
        "\n\n".join(notes)
        if notes
        else "No readable Word, PDF or text content was found."
    )


BOLD_MARK = re.compile(r"\*\*(.+?)\*\*")
CODE_MARK = re.compile(r"`([^`]+)`")
HEADING_LINE = re.compile(r"^(#{1,6})(?:\s+(.*))?$")


def format_inline_html(text: str) -> str:
    text = escape(text)
    text = BOLD_MARK.sub(r"<strong>\1</strong>", text)
    return CODE_MARK.sub(r"<code>\1</code>", text)


def format_message_html(content: str) -> str:
    chunks: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            chunks.append("<br>".join(paragraph))
            paragraph.clear()

    for raw in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        heading = HEADING_LINE.match(raw.rstrip())
        if heading:
            title = (heading.group(2) or "").strip().rstrip("#").strip()
            if not title:
                continue
            flush_paragraph()
            level = min(len(heading.group(1)), 6)
            chunks.append(
                f'<span class="chat-md-h{level}">{format_inline_html(title)}</span>'
            )
            continue
        paragraph.append(format_inline_html(raw) if raw else "")
    flush_paragraph()
    return "".join(chunks)


def chat_thread_html(topic: str, *, hide_active: bool = False) -> str:
    def assistant_body_html(message: dict[str, str]) -> str:
        content = message.get("content") or ""
        status = message.get("status")
        generating = status == "generating" or (
            content.startswith("This answer is being generated by")
            and "\n\n" not in content
        )
        if generating:
            return TYPING_DOTS
        if status == "streaming":
            return format_message_html(content) + '<span class="gpt-caret"></span>'
        if (
            "This answer is being generated by" in content
            or "This answer is generated by" in content
        ):
            note, sep, body = content.partition("\n\n")
            note_html = format_message_html(note)
            body_html = format_message_html(body.lstrip("\n")) if sep else ""
            if body_html:
                return (
                    f'<span class="model-chat-source">{note_html}</span>'
                    f"{body_html}"
                )
            return f'<span class="model-chat-source">{note_html}</span>'
        return format_message_html(content)

    messages = st.session_state.get(chat_key(topic), [])
    if not messages:
        return ""
    rows: list[str] = []
    for message in messages:
        if hide_active and message.get("status") in {"generating", "streaming"}:
            continue
        if message["role"] == "user":
            text = format_message_html(message["content"])
            rows.append(
                '<div class="model-chat-row model-chat-row--user">'
                f'<div class="model-chat-bubble model-chat-bubble--user">{text}</div>'
                '<span class="model-chat-avatar model-chat-avatar--user" aria-hidden="true">U</span>'
                "</div>"
            )
            continue
        company = st.session_state.get("rlhf_company")
        mark_company = message.get("company") or company
        if topic == "RLHF-aligned Model" and mark_company in RLHF_CATALOG:
            mark = company_mark(mark_company, "#111111")
        elif topic in LLAMA_TOPICS:
            mark = company_mark("Meta", "#111111")
        else:
            mark = ASSISTANT_MARK
        rows.append(
            '<div class="model-chat-row model-chat-row--assistant">'
            f'<span class="model-chat-avatar model-chat-avatar--assistant" aria-hidden="true">{mark}</span>'
            f'<div class="model-chat-bubble model-chat-bubble--assistant">{assistant_body_html(message)}</div>'
            "</div>"
        )
    return "".join(rows)


def rlhf_bar_html() -> str:
    company = ensure_rlhf_company()
    model = st.session_state.get("rlhf_model")
    models = RLHF_CATALOG[company]
    locked = rlhf_busy()
    caret = '<span class="rlhf-caret-btn" aria-hidden="true"></span>'
    capsules = "".join(
        (
            f'<span class="rlhf-capsule'
            f'{" is-active" if name == company else ""}" role="button" tabindex="0" '
            f'data-rlhf-company="{escape(name)}">'
            f"{company_mark(name, '#111111' if name == company else '#ffffff')}"
            f"<span>{escape(name)}</span></span>"
        )
        for name in RLHF_CATALOG
    )
    model_label = model if model in models else "Select model"
    model_toggle = (
        f"{company_mark(company, '#ffffff')}"
        f"<span>{escape(model_label)}</span>{caret}"
    )
    model_items = "".join(
        (
            f'<span class="rlhf-dd-item'
            f'{" is-active" if label == model else ""}" role="button" tabindex="0" '
            f'data-rlhf-model="{escape(model_widget_id(model_id))}">'
            f"{company_mark(company, '#ffffff')}<span>{escape(label)}</span></span>"
        )
        for label, model_id in models.items()
    )
    if locked:
        model_control = (
            "<div class='rlhf-dd'>"
            "<div class='rlhf-dd-toggle'>"
            f"{model_toggle}"
            "</div>"
            "</div>"
        )
    else:
        model_control = (
            "<details class='rlhf-dd'>"
            "<summary class='rlhf-dd-toggle'>"
            f"{model_toggle}"
            "</summary>"
            f"<div class='rlhf-dd-menu'>{model_items}</div>"
            "</details>"
        )
    openai_controls = ""
    if company == "OpenAI":
        openai_controls = f"{control_mode_html(locked)}{controls_html(locked)}"
    return (
        f"<div class='rlhf-bar{' is-locked' if locked else ''}'>"
        "<div class='rlhf-bar-left'>"
        "<span class='model-chat-title'>AI assistant</span>"
        "</div>"
        "<div class='rlhf-menus'>"
        f"<div class='rlhf-switch' role='tablist' aria-label='Company'>{capsules}</div>"
        f"{model_control}"
        f"{openai_controls}"
        "<span class='rlhf-clear' role='button' tabindex='0' data-rlhf-clear='1'>Clear</span>"
        "</div>"
        "</div>"
    )


def control_mode_html(locked: bool) -> str:
    mode = ensure_control_mode()
    capsules = "".join(
        (
            f'<span class="rlhf-capsule'
            f'{" is-active" if name == mode else ""}" role="button" tabindex="0" '
            f'data-rlhf-mode="{escape(name)}">{escape(name)}</span>'
        )
        for name in ("Auto", "Manual")
    )
    cls = "rlhf-switch rlhf-mode-switch"
    if locked:
        cls += " is-locked"
    return (
        f"<div class='{cls}' role='tablist' aria-label='Control'>"
        "<span class='rlhf-mode-brand'>Control</span>"
        f"{capsules}"
        "</div>"
    )


def _control_card(title: str, items: str) -> str:
    return (
        "<div class='rlhf-length-card'>"
        f"<div class='rlhf-length-title'>{escape(title)}</div>"
        f"{items}"
        "</div>"
    )


def _control_options(kind: str, labels: list[str], current: str, hints: dict[str, str] | None = None) -> str:
    hints = hints or {}
    return "".join(
        (
            f'<span class="rlhf-length-item'
            f'{" is-active" if label == current else ""}" role="button" tabindex="0" '
            f'data-rlhf-pick="{escape(kind)}" data-rlhf-value="{escape(label)}">'
            f'<span class="rlhf-length-name">{escape(label)}</span>'
            + (
                f'<span class="rlhf-length-hint">{escape(hints[label])}</span>'
                if label in hints
                else ""
            )
            + "</span>"
        )
        for label in labels
    )


def _enabled_row(kind: str, label: str, current: str, title: str, items: str) -> str:
    return (
        f"<details class='rlhf-control-flyout' data-rlhf-row='{escape(kind)}'>"
        "<summary class='rlhf-control-row'>"
        "<span class='rlhf-caret-next' aria-hidden='true'></span>"
        f"<span class='rlhf-control-current'>{escape(current)}</span>"
        f"<span class='rlhf-control-label'>{escape(label)}</span>"
        "</summary>"
        f"{_control_card(title, items)}"
        "</details>"
    )


def _disabled_row(label: str, note: str) -> str:
    return (
        "<div class='rlhf-control-row is-disabled'>"
        f"<span class='rlhf-control-current'>{escape(note)}</span>"
        f"<span class='rlhf-control-label'>{escape(label)}</span>"
        "</div>"
    )


def controls_html(locked: bool) -> str:
    if ensure_control_mode() != "Manual":
        return ""
    ensure_controls()
    spec = spec_for(current_control_model())
    caret = '<span class="rlhf-caret-btn" aria-hidden="true"></span>'
    toggle_label = "Controls ✓" if controls_ready_for_request() else "Controls"
    toggle = f"<span>{toggle_label}</span>{caret}"
    tokens = ensure_output_length()
    reasoning = ensure_reasoning()
    verbosity = ensure_verbosity()
    temperature = ensure_temperature()
    temp_label = "Auto" if temperature is None else f"{temperature:.1f}"

    if spec.disabled or not spec.max_tokens:
        tokens_row = _disabled_row("Max tokens", "Not supported")
    else:
        tokens_row = _enabled_row(
            "tok",
            "Max tokens",
            tokens,
            "Output length",
            _control_options("tok", list(OUTPUT_LENGTHS), tokens, OUTPUT_LENGTH_HINTS),
        )

    if spec.disabled or not spec.reasoning:
        reasoning_row = _disabled_row("Reasoning", "Not supported")
    else:
        reasoning_row = _enabled_row(
            "rsn",
            "Reasoning",
            reasoning,
            "Reasoning",
            _control_options("rsn", list(spec.reasoning), reasoning),
        )

    if spec.disabled or not spec.verbosity:
        verbosity_row = _disabled_row("Verbosity", "Not supported")
    else:
        verbosity_row = _enabled_row(
            "vrb",
            "Verbosity",
            verbosity,
            "Verbosity",
            _control_options("vrb", VERBOSITY_OPTIONS, verbosity),
        )

    if spec.disabled or spec.temperature is None:
        temperature_row = _disabled_row("Temperature", "Not supported")
    else:
        manual = temperature is not None
        slider_hidden = "" if manual else " is-hidden"
        slider = (
            '<div class="rlhf-temp-modes">'
            f'<span class="rlhf-temp-mode{" is-active" if not manual else ""}" '
            'role="button" tabindex="0" data-rlhf-temp-mode="Auto">Auto</span>'
            f'<span class="rlhf-temp-mode{" is-active" if manual else ""}" '
            'role="button" tabindex="0" data-rlhf-temp-mode="Manual">Manual</span>'
            "</div>"
            f'<div class="rlhf-temp-slider{slider_hidden}">'
            '<span class="rlhf-temp-ends">0</span>'
            '<input type="range" min="0" max="2" step="0.1" '
            f'value="{0.7 if temperature is None else temperature}" '
            'data-rlhf-temp-range="1">'
            '<span class="rlhf-temp-ends">2</span>'
            f'<span class="rlhf-temp-readout">{0.7 if temperature is None else f"{temperature:.1f}"}</span>'
            "</div>"
        )
        enabled = _enabled_row("tmp", "Temperature", temp_label, "Temperature", slider)
        if spec.temperature == "reasoning_none":
            locked_display = "none" if reasoning == "None" else "block"
            enabled_display = "block" if reasoning == "None" else "none"
            temperature_row = (
                '<div class="rlhf-temp-block" data-temp-policy="reasoning_none">'
                f'<div data-temp-enabled="1" style="display:{enabled_display}">{enabled}</div>'
                f'<div data-temp-locked="1" style="display:{locked_display}">'
                f'{_disabled_row("Temperature", "Available only with Reasoning: None")}'
                "</div>"
                "</div>"
            )
        else:
            temperature_row = (
                '<div class="rlhf-temp-block" data-temp-policy="range">'
                f"{enabled}"
                "</div>"
            )

    ok = (
        "<span class='rlhf-ctrl-ok' role='button' tabindex='0' data-rlhf-ctrl-ok='1'>OK</span>"
        if not spec.disabled
        else ""
    )
    menu = tokens_row + reasoning_row + verbosity_row + temperature_row + ok
    if locked:
        return (
            "<div class='rlhf-dd rlhf-controls'>"
            f"<div class='rlhf-dd-toggle'>{toggle}</div>"
            "</div>"
        )
    return (
        "<details class='rlhf-dd rlhf-controls'>"
        f"<summary class='rlhf-dd-toggle'>{toggle}</summary>"
        f"<div class='rlhf-dd-menu'>{menu}</div>"
        "</details>"
    )


def _format_control_number(value: float, digits: int) -> str:
    text = f"{value:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _slider_card(
    *,
    kind: str,
    current: float | None,
    default: float,
    minimum: float,
    maximum: float,
    step: float,
    digits: int,
) -> str:
    manual = current is not None
    value = default if current is None else current
    shown = _format_control_number(value, digits)
    slider_hidden = "" if manual else " is-hidden"
    return (
        '<div class="rlhf-temp-modes">'
        f'<span class="rlhf-temp-mode{" is-active" if not manual else ""}" '
        f'role="button" tabindex="0" data-range-choice="Auto" data-range-kind="{escape(kind)}">Auto</span>'
        f'<span class="rlhf-temp-mode{" is-active" if manual else ""}" '
        f'role="button" tabindex="0" data-range-choice="Manual" data-range-kind="{escape(kind)}">Manual</span>'
        "</div>"
        f'<div class="rlhf-temp-slider{slider_hidden}">'
        f'<span class="rlhf-temp-ends">{_format_control_number(minimum, digits)}</span>'
        f'<input type="range" min="{minimum}" max="{maximum}" step="{step}" '
        f'value="{value}" data-range-input="{escape(kind)}" data-range-digits="{digits}">'
        f'<span class="rlhf-temp-ends">{_format_control_number(maximum, digits)}</span>'
        f'<span class="rlhf-temp-readout">{shown}</span>'
        "</div>"
    )


def llama_control_mode_html(topic: str, locked: bool) -> str:
    mode = ensure_llama_control_mode(topic)
    capsules = "".join(
        (
            f'<span class="rlhf-capsule'
            f'{" is-active" if name == mode else ""}" role="button" tabindex="0" '
            f'data-llama-mode="{escape(name)}">{escape(name)}</span>'
        )
        for name in ("Auto", "Manual")
    )
    cls = "rlhf-switch rlhf-mode-switch"
    if locked:
        cls += " is-locked"
    return (
        f"<div class='{cls}' role='tablist' aria-label='Control'>"
        "<span class='rlhf-mode-brand'>Control</span>"
        f"{capsules}"
        "</div>"
    )


def llama_controls_html(topic: str, locked: bool) -> str:
    if ensure_llama_control_mode(topic) != "Manual":
        return ""
    ensure_llama_controls(topic)
    caret = '<span class="rlhf-caret-btn" aria-hidden="true"></span>'
    toggle_label = "Controls ✓" if llama_controls_ready_for_request(topic) else "Controls"
    toggle = f"<span>{toggle_label}</span>{caret}"
    tokens = ensure_llama_output_length(topic)
    temperature = ensure_llama_temperature(topic)
    top_p = ensure_llama_top_p(topic)
    frequency = ensure_llama_frequency_penalty(topic)
    tokens_row = _enabled_row(
        "tok",
        "Max tokens",
        tokens,
        "Output length",
        _control_options("tok", list(OUTPUT_LENGTHS), tokens, OUTPUT_LENGTH_HINTS),
    )
    temperature_row = _enabled_row(
        "tmp",
        "Temperature",
        "Auto" if temperature is None else _format_control_number(temperature, 1),
        "Temperature",
        _slider_card(
            kind="tmp",
            current=temperature,
            default=DEFAULT_TEMPERATURE,
            minimum=0,
            maximum=2,
            step=0.1,
            digits=1,
        ),
    )
    top_p_row = _enabled_row(
        "topp",
        "Top P",
        "Auto" if top_p is None else _format_control_number(top_p, 2),
        "Top P",
        _slider_card(
            kind="topp",
            current=top_p,
            default=DEFAULT_TOP_P,
            minimum=0,
            maximum=1,
            step=0.05,
            digits=2,
        ),
    )
    frequency_row = _enabled_row(
        "freq",
        "Freq penalty",
        "Auto" if frequency is None else _format_control_number(frequency, 1),
        "Frequency penalty",
        _slider_card(
            kind="freq",
            current=frequency,
            default=DEFAULT_FREQUENCY_PENALTY,
            minimum=-2,
            maximum=2,
            step=0.1,
            digits=1,
        ),
    )
    ok = (
        "<span class='rlhf-ctrl-ok' role='button' tabindex='0' data-llama-ctrl-ok='1'>OK</span>"
    )
    menu = tokens_row + temperature_row + top_p_row + frequency_row + ok
    if locked:
        return (
            "<div class='rlhf-dd rlhf-controls'>"
            f"<div class='rlhf-dd-toggle'>{toggle}</div>"
            "</div>"
        )
    return (
        "<details class='rlhf-dd rlhf-controls'>"
        f"<summary class='rlhf-dd-toggle'>{toggle}</summary>"
        f"<div class='rlhf-dd-menu'>{menu}</div>"
        "</details>"
    )


def llama_bar_html(topic: str) -> str:
    locked = llama_busy(topic)
    brand = (
        "<span class='model-chat-brand'>"
        f"{company_mark('Meta', '#ffffff')}"
        "<span class='model-chat-title'>Llama</span>"
        "</span>"
    )
    extras = f"{llama_control_mode_html(topic, locked)}{llama_controls_html(topic, locked)}"
    return (
        f"<div class='rlhf-bar{' is-locked' if locked else ''}' data-llama-scope='{llama_scope(topic)}'>"
        f"<div class='rlhf-bar-left'>{brand}</div>"
        "<div class='rlhf-menus'>"
        f"{extras}"
        "<span class='rlhf-clear' role='button' tabindex='0' data-llama-clear='1'>Clear</span>"
        "</div>"
        "</div>"
    )


def render_rlhf_buttons() -> None:
    models = RLHF_CATALOG[ensure_rlhf_company()]
    with st.container(key="rlhf_picker", gap=None):
        for name in RLHF_CATALOG:
            st.button(
                name,
                key=f"rlhf_co_{name}",
                on_click=select_rlhf_company,
                args=(name,),
            )
        for label, model_id in models.items():
            st.button(
                label,
                key=f"rlhf_md_{model_widget_id(model_id)}",
                on_click=select_rlhf_model,
                args=(label,),
            )
        for name in ("Auto", "Manual"):
            st.button(
                name,
                key=f"rlhf_mode_{name}",
                on_click=select_control_mode,
                args=(name,),
            )
        st.button("Clear", key="rlhf_clear", on_click=clear_rlhf_chat)
        st.button(
            "Stop",
            key="chat_stop",
            on_click=request_chat_stop,
            args=("RLHF-aligned Model",),
        )
        with st.form("rlhf_ctrl_form", border=False):
            st.text_area(
                "controls_draft",
                key="rlhf_controls_draft",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button(
                "Apply controls",
                key="rlhf_ctrl_ok",
            )
        if submitted:
            apply_control_draft()


def render_llama_buttons(topic: str) -> None:
    slot = llama_scope(topic)
    with st.container(key=f"llama_picker_{slot}", gap=None):
        for name in ("Auto", "Manual"):
            st.button(
                name,
                key=f"llama_mode_{slot}_{name}",
                on_click=select_llama_control_mode,
                args=(topic, name),
            )
        st.button(
            "Clear",
            key=f"llama_clear_{slot}",
            on_click=clear_llama_chat,
            args=(topic,),
        )
        st.button(
            "Stop",
            key="chat_stop",
            on_click=request_chat_stop,
            args=(topic,),
        )
        with st.form(f"llama_ctrl_form_{slot}", border=False):
            st.text_area(
                "controls_draft",
                key=llama_key(topic, "controls_draft"),
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button(
                "Apply controls",
                key=f"llama_ctrl_ok_{slot}",
            )
        if submitted:
            apply_llama_control_draft(topic)


def render(
    lecture: str | None,
    sub_lecture: str | None,
    topic: str,
    *,
    crumbs: str,
) -> None:
    number = (lecture or "5").split()[-1]
    is_rlhf = topic == "RLHF-aligned Model"
    is_llama = topic in LLAMA_TOPICS
    if is_rlhf:
        recover_rlhf_lock()
        ensure_rlhf_company()
        apply_scheduled_control_reset()
        ensure_control_mode()
        ensure_controls()
        if not rlhf_busy():
            settle_partial_assistant(topic)
    elif is_llama:
        recover_llama_lock(topic)
        apply_scheduled_llama_control_reset(topic)
        ensure_llama_control_mode(topic)
        ensure_llama_controls(topic)
        if not llama_busy(topic):
            settle_partial_assistant(topic)
    key = chat_key(topic)
    st.session_state.setdefault(key, [])
    ready = (not is_rlhf) or rlhf_ready()

    with st.container(key="lesson_block", gap=None):
        header_html = (
            "<div class='lesson-block-header'>"
            f"<div class='lesson-number'>{escape(number)}</div>"
            f"{crumbs}"
            "</div>"
        )
        if is_rlhf:
            render_rlhf_buttons()
            topbar_html = rlhf_bar_html()
        else:
            render_llama_buttons(topic)
            topbar_html = llama_bar_html(topic)
        pending = None
        if is_rlhf and rlhf_busy():
            pending = st.session_state.get("rlhf_pending")
        elif is_llama and llama_busy(topic):
            pending = llama_pending(topic)
        if pending and pending.get("type") == "files":
            ingest_result = ingest_uploads(topic, pending.get("files") or [])
            pending = {
                **pending,
                "ingest_result": ingest_result,
                "files": [],
            }
            if str(pending.get("text") or "").strip():
                pending["type"] = "text"
            st.session_state.rlhf_pending = pending
        live_openai = bool(
            pending
            and pending.get("type") != "files"
            and pending.get("company") == "OpenAI"
            and pending.get("model") in RLHF_CATALOG.get("OpenAI", {})
        )

        def lesson_html() -> str:
            generating = (
                (is_rlhf and rlhf_busy()) or (is_llama and llama_busy(topic))
            )
            flag = "1" if generating else "0"
            scope_attr = (
                f" data-llama-scope='{llama_scope(topic)}'" if is_llama else ""
            )
            return (
                f"<div class='model-chat-shell' data-generating='{flag}'{scope_attr}>"
                f"{header_html}"
                f"{topbar_html}"
                "<div class='model-chat'>"
                "<div class='model-chat-thread'>"
                f"{chat_thread_html(topic)}"
                "</div>"
                "</div>"
                "</div>"
            )

        shell = st.empty()
        shell.html(lesson_html())
        controls_ready = True
        if is_rlhf:
            controls_ready = controls_ready_for_request()
        elif is_llama:
            controls_ready = llama_controls_ready_for_request(topic)
        if is_rlhf and ready and not controls_ready:
            placeholder = "Set Manual controls and press OK before sending"
        elif is_rlhf and ready:
            company = ensure_rlhf_company()
            model = st.session_state.get("rlhf_model")
            placeholder = f"Ask a question for {company}'s {model}"
        elif ready:
            placeholder = (
                "Ask a question for Meta's Llama"
                if topic in LLAMA_TOPICS
                else "Ask a question"
            )
        else:
            placeholder = "Select a company and model above"
        prompt = st.chat_input(
            placeholder,
            key=f"chat_input_{topic}",
            disabled=(
                (not ready)
                or (is_rlhf and rlhf_busy())
                or (is_rlhf and not controls_ready)
                or (is_llama and llama_busy(topic))
                or (is_llama and not controls_ready)
            ),
            accept_file=True,
            file_type=UPLOAD_FILE_TYPES,
        )
        if live_openai:
            history = st.session_state[key]
            company = pending.get("company") or ensure_rlhf_company()
            model = pending.get("model") or st.session_state.get("rlhf_model")
            models = RLHF_CATALOG.get(company or "", {})
            document = st.session_state.get(doc_context_key(topic), "")
            acc = ""
            last_paint = 0.0
            if history and history[-1]["role"] == "assistant":
                history[-1]["status"] = "streaming"
                history[-1]["company"] = company
            finished = False
            try:
                api_controls = controls_from_pending(pending, model)
                print(
                    "[RLHF REQUEST]",
                    "model=",
                    models[model],
                    "controls=",
                    api_controls,
                )
                for token in openai_stream_tokens(
                    models[model],
                    api_messages(history),
                    document=document,
                    controls=api_controls,
                ):
                    acc += token
                    if history and history[-1]["role"] == "assistant":
                        history[-1]["content"] = with_rlhf_note(topic, acc, done=False)
                        history[-1]["status"] = "streaming"
                    now = time.monotonic()
                    if last_paint == 0.0 or now - last_paint >= 0.05:
                        shell.html(lesson_html())
                        last_paint = now
                finished = True
            finally:
                commit_assistant(history, topic, acc, company=company)
                st.session_state.rlhf_pending = None
                st.session_state.rlhf_busy = False
            if finished:
                schedule_control_reset()
                st.rerun()
        live_llama = bool(
            is_llama
            and pending
            and pending.get("type") != "files"
        )
        if live_llama:
            history = st.session_state[key]
            document = st.session_state.get(doc_context_key(topic), "")
            acc = ""
            last_paint = 0.0
            if history and history[-1]["role"] == "assistant":
                history[-1]["status"] = "streaming"
            finished = False
            model_id = (
                LLAMA_INSTRUCT_MODEL
                if topic == "Fine-tuned Model"
                else LLAMA_BASE_MODEL
            )
            kind = "instruct" if topic == "Fine-tuned Model" else "base"
            api_controls = llama_controls_from_pending(pending)
            try:
                for token in llama_stream_tokens(
                    model_id,
                    api_messages(history),
                    document=document,
                    kind=kind,
                    topic=topic,
                    controls=api_controls,
                ):
                    acc += token
                    if history and history[-1]["role"] == "assistant":
                        history[-1]["content"] = with_rlhf_note(
                            topic, acc, done=False
                        )
                        history[-1]["status"] = "streaming"
                    now = time.monotonic()
                    if last_paint == 0.0 or now - last_paint >= 0.05:
                        shell.html(lesson_html())
                        last_paint = now
                finished = True
            finally:
                commit_assistant(history, topic, acc)
                set_llama_run(topic, busy=False)
            if finished:
                schedule_llama_control_reset(topic)
                st.rerun()
        if is_rlhf and rlhf_busy() and st.session_state.get("rlhf_pending"):
            history = st.session_state[key]
            pending = st.session_state.rlhf_pending
            company = pending.get("company") or ensure_rlhf_company()
            model = pending.get("model") or st.session_state.get("rlhf_model")
            if pending.get("type") == "files":
                body = pending.get("ingest_result") or ingest_uploads(
                    topic, pending.get("files") or []
                )
            else:
                body = model_reply(
                    topic,
                    history,
                    company=company,
                    model=model,
                    output_length=pending.get("output_length"),
                    reasoning=pending.get("reasoning"),
                    verbosity=pending.get("verbosity"),
                    temperature=pending.get("temperature"),
                    control_mode=pending.get("control_mode"),
                )
            reply = with_rlhf_note(topic, body, done=True)
            if history and history[-1]["role"] == "assistant":
                history[-1]["content"] = reply
                history[-1]["company"] = company
                history[-1]["status"] = "done"
            else:
                history.append(
                    {
                        "role": "assistant",
                        "content": reply,
                        "company": company,
                        "status": "done",
                    }
                )
            st.session_state.rlhf_pending = None
            st.session_state.rlhf_busy = False
            if pending.get("type") != "files":
                schedule_control_reset()
            st.rerun()
        if prompt and not (is_rlhf and rlhf_busy()) and not (is_llama and llama_busy(topic)):
            history = st.session_state[key]
            if isinstance(prompt, str):
                text, files = prompt.strip(), []
            else:
                text = (prompt.text or "").strip()
                files = list(getattr(prompt, "files", None) or [])
            request_controls: dict = {}
            if files:
                accepted, rejected = split_uploads(files)
                if rejected:
                    names = ", ".join(
                        getattr(item, "name", "file") for item in rejected
                    )
                    history.append(
                        {
                            "role": "user",
                            "content": (
                                f"{text}\n[{names}]" if text else f"Uploaded {names}"
                            ),
                        }
                    )
                    history.append(
                        {"role": "assistant", "content": UPLOAD_REJECT}
                    )
                    st.rerun()
                files = accepted
            if files or text:
                if is_rlhf:
                    frozen = control_snapshot()
                    if frozen is None:
                        st.rerun()
                    request_controls = frozen
                elif is_llama:
                    frozen = llama_control_snapshot(topic)
                    if frozen is None:
                        st.rerun()
                    request_controls = frozen
                else:
                    request_controls = {}
            if files:
                names = ", ".join(getattr(item, "name", "file") for item in files)
                history.append(
                    {
                        "role": "user",
                        "content": f"{text}\n[{names}]" if text else f"Uploaded {names}",
                    }
                )
                if is_rlhf:
                    company = ensure_rlhf_company()
                    history.append(
                        {
                            "role": "assistant",
                            "content": "",
                            "company": company,
                            "status": "generating",
                        }
                    )
                    st.session_state.rlhf_pending = {
                        "type": "files",
                        "files": files,
                        "text": text,
                        "company": company,
                        "model": st.session_state.get("rlhf_model"),
                        **request_controls,
                    }
                    st.session_state.rlhf_busy = True
                    st.rerun()
                ingest_result = ingest_uploads(topic, files)
                if not text:
                    history.append(
                        {
                            "role": "assistant",
                            "content": with_rlhf_note(topic, ingest_result),
                        }
                    )
                    st.rerun()
                history.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "status": "generating",
                    }
                )
                set_llama_run(topic, busy=True, pending={"type": "text", **request_controls})
                st.rerun()
            elif text:
                history.append({"role": "user", "content": text})
                if is_rlhf:
                    company = ensure_rlhf_company()
                    history.append(
                        {
                            "role": "assistant",
                            "content": "",
                            "company": company,
                            "status": "generating",
                        }
                    )
                    st.session_state.rlhf_pending = {
                        "type": "text",
                        "company": company,
                        "model": st.session_state.get("rlhf_model"),
                        **request_controls,
                    }
                    st.session_state.rlhf_busy = True
                    st.rerun()
                history.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "status": "generating",
                    }
                )
                set_llama_run(topic, busy=True, pending={"type": "text", **request_controls})
                st.rerun()
