from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STYLES = ROOT / "styles" / "app.css"
FAVICON = ASSETS / "favicon.svg"

BITSOM_LOGO = (
    "https://www.bitsom.edu.in/wp-content/uploads/2023/04/zero_scroll_logo-icn-1.svg"
)

LECTURES = [f"Lecture {n}" for n in range(1, 11)]
SUB_LECTURES = {
    "Lecture 5": ["Tokenisation", "Input context", "Post Training"],
}
TOPICS = {
    ("Lecture 5", "Post Training"): [
        "Base Model",
        "Fine-tuned Model",
        "RLHF-aligned Model",
    ],
}


def inject_css() -> None:
    css = STYLES.read_text(encoding="utf-8")
    st.html(
        "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500&display=swap'>"
        f"<style>{css}</style>"
        """
        <script>
        (function () {
          if (window.__crumbForward) return;
          window.__crumbForward = true;
          document.addEventListener("click", function (e) {
            var crumb = e.target.closest(".crumb-link");
            if (!crumb) return;
            e.preventDefault();
            var level = crumb.getAttribute("data-level") || "lecture";
            var btn = document.querySelector('[class*="st-key-crumb_' + level + '"] button');
            if (btn) btn.click();
          }, true);
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def lock_dropdowns() -> None:
    components.html(
        """
        <script>
        (function () {
          const root = window.parent.document;
          const win = root.defaultView;
          const allow = new Set(["ArrowDown", "ArrowUp", "Enter", "Escape", "Tab", "Home", "End"]);

          function lockInput(el) {
            el.setAttribute("readonly", "readonly");
            el.setAttribute("inputmode", "none");
            el.setAttribute("autocomplete", "off");
            el.style.caretColor = "transparent";
            if (el.dataset.dropdownLocked === "1") return;
            el.dataset.dropdownLocked = "1";

            function block(e) {
              if (e.type === "keydown" && allow.has(e.key)) return;
              e.preventDefault();
              e.stopImmediatePropagation();
            }

            ["keydown", "keypress", "beforeinput", "paste", "cut", "drop"].forEach(function (type) {
              el.addEventListener(type, block, true);
            });
          }

          function wireOpenOnClick(select) {
            if (select.dataset.fullClick === "1") return;
            select.dataset.fullClick = "1";
            select.addEventListener("click", function (e) {
              if (select.querySelector("input:disabled")) return;
              if (select.getAttribute("aria-disabled") === "true") return;
              if (e.target.closest("svg")) return;

              const svgs = select.querySelectorAll("svg");
              let chevron = null;
              svgs.forEach(function (svg) {
                const path = svg.querySelector("path");
                const d = path ? path.getAttribute("d") || "" : "";
                if (d.indexOf("M12 2C6.47") === -1) chevron = svg;
              });
              if (!chevron && svgs.length) chevron = svgs[svgs.length - 1];
              if (!chevron) return;

              const host = chevron.closest("button") || chevron.parentElement;
              ["mousedown", "mouseup", "click"].forEach(function (type) {
                host.dispatchEvent(new win.MouseEvent(type, { bubbles: true, cancelable: true, view: win }));
              });
            });
          }

          function scan() {
            root.querySelectorAll('[data-testid="stSelectbox"] input, [data-baseweb="select"] input').forEach(lockInput);
            root.querySelectorAll('[data-baseweb="select"]').forEach(wireOpenOnClick);
          }

          if (!root.documentElement.dataset.crumbForward) {
            root.documentElement.dataset.crumbForward = "1";
            root.addEventListener("click", function (e) {
              const crumb = e.target.closest(".crumb-link");
              if (!crumb) return;
              e.preventDefault();
              const level = crumb.getAttribute("data-level") || "lecture";
              const btn = root.querySelector('[class*="st-key-crumb_' + level + '"] button');
              if (btn) btn.click();
            }, true);
          }

          scan();
          new MutationObserver(scan).observe(root.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def clear_sub_lecture() -> None:
    st.session_state.sub_lecture_select = None
    st.session_state.topic_select = None


def clear_topic() -> None:
    st.session_state.topic_select = None


def breadcrumb_html(
    lecture: str | None, sub_lecture: str | None, topic: str | None
) -> str:
    if not lecture:
        return ""
    parts: list[str] = []
    if sub_lecture:
        parts.append(
            f'<span class="crumb-link" role="button" tabindex="0" data-level="lecture">{lecture}</span>'
        )
        parts.append('<span class="crumb-sep">&gt;</span>')
        if topic:
            parts.append(
                f'<span class="crumb-link" role="button" tabindex="0" data-level="sub">{sub_lecture}</span>'
            )
            parts.append('<span class="crumb-sep">&gt;</span>')
            parts.append(f'<span class="crumb-current">{topic}</span>')
        else:
            parts.append(f'<span class="crumb-current">{sub_lecture}</span>')
    else:
        parts.append(f'<span class="crumb-current">{lecture}</span>')
    return f'<nav class="lesson-crumb" aria-label="Location">{"".join(parts)}</nav>'


def render_crumbs(lecture: str | None, sub_lecture: str | None, topic: str | None) -> None:
    if lecture and sub_lecture:
        st.button(
            lecture,
            key="crumb_lecture",
            type="tertiary",
            on_click=clear_sub_lecture,
        )
    if lecture and sub_lecture and topic:
        st.button(
            sub_lecture,
            key="crumb_sub",
            type="tertiary",
            on_click=clear_topic,
        )


ASSISTANT_MARK = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="#111111" d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/>'
    "</svg>"
)


def chat_key(topic: str) -> str:
    return f"chat_messages::{topic}"


def model_reply(topic: str, messages: list[dict[str, str]]) -> str:
    _ = messages
    if topic == "Base Model":
        return "Base Model will answer once connected to Hugging Face."
    if topic == "Fine-tuned Model":
        return "Fine-tuned Model will answer once connected to Hugging Face."
    return f"{topic} will answer here once its API is connected."


FILE_READERS = {
    ".pdf": "pypdf",
    ".doc": "python-docx",
    ".docx": "python-docx",
    ".ppt": "python-pptx",
    ".pptx": "python-pptx",
    ".xls": "openpyxl",
    ".xlsx": "openpyxl",
    ".csv": "pandas",
    ".txt": "built-in Python file I/O",
    ".md": "built-in Python file I/O",
}


def file_reader_reply(files: list) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    for uploaded in files:
        ext = Path(getattr(uploaded, "name", "")).suffix.lower()
        label = ext.lstrip(".").upper() or "this file"
        lib = FILE_READERS.get(ext, "the matching Python reader")
        item = f"{label} with {lib}"
        if item not in seen:
            seen.add(item)
            lines.append(item)
    detail = ", ".join(lines) if lines else "DOC, PDF, and similar formats"
    return (
        "File received. Next we will wire the Python libraries that read "
        f"{detail}."
    )


def chat_thread_html(topic: str) -> str:
    messages = st.session_state.get(chat_key(topic), [])
    if not messages:
        return ""
    rows: list[str] = []
    for message in messages:
        text = escape(message["content"]).replace("\n", "<br>")
        if message["role"] == "user":
            rows.append(
                '<div class="model-chat-row model-chat-row--user">'
                f'<div class="model-chat-bubble model-chat-bubble--user">{text}</div>'
                '<span class="model-chat-avatar model-chat-avatar--user" aria-hidden="true">U</span>'
                "</div>"
            )
        else:
            rows.append(
                '<div class="model-chat-row model-chat-row--assistant">'
                f'<span class="model-chat-avatar model-chat-avatar--assistant" aria-hidden="true">{ASSISTANT_MARK}</span>'
                f'<div class="model-chat-bubble model-chat-bubble--assistant">{text}</div>'
                "</div>"
            )
    return "".join(rows)


def render_header() -> None:
    st.markdown(
        f"""
        <header class="lecture-header">
          <div class="lecture-header-inner">
            <div class="lecture-header-logo">
              <img src="{BITSOM_LOGO}" alt="BITSoM Logo" />
            </div>
            <div class="lecture-header-text">
              <span class="lecture-header-title">AI Course</span>
              <span class="lecture-header-sub">Foundations of AI</span>
            </div>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_chat(lecture: str | None, sub_lecture: str | None, topic: str) -> None:
    crumbs = breadcrumb_html(lecture, sub_lecture, topic)
    number = (lecture or "5").split()[-1]
    key = chat_key(topic)
    st.session_state.setdefault(key, [])

    with st.container(key="lesson_block", gap=None):
        st.html(
            "<div class='model-chat-shell'>"
            "<div class='lesson-block-header'>"
            f"<div class='lesson-number'>{escape(number)}</div>"
            f"{crumbs}"
            "</div>"
            "<div class='model-chat'>"
            "<div class='model-chat-topbar'>"
            "<span class='model-chat-title'>AI assistant</span>"
            "<span class='model-chat-status'>online</span>"
            "</div>"
            "<div class='model-chat-thread'>"
            f"{chat_thread_html(topic)}"
            "</div>"
            "</div>"
            "</div>"
        )
        prompt = st.chat_input(
            "Ask a question",
            key=f"chat_input_{topic}",
            accept_file=True,
            file_type=["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "csv", "txt", "md"],
        )
        if prompt:
            history = st.session_state[key]
            if isinstance(prompt, str):
                text, files = prompt.strip(), []
            else:
                text = (prompt.text or "").strip()
                files = list(getattr(prompt, "files", None) or [])
            if files:
                names = ", ".join(getattr(item, "name", "file") for item in files)
                history.append(
                    {
                        "role": "user",
                        "content": f"{text}\n[{names}]" if text else f"Uploaded {names}",
                    }
                )
                history.append({"role": "assistant", "content": file_reader_reply(files)})
                st.rerun()
            elif text:
                history.append({"role": "user", "content": text})
                history.append({"role": "assistant", "content": model_reply(topic, history)})
                st.rerun()
    render_crumbs(lecture, sub_lecture, topic)


def render_workspace(
    lecture: str | None, sub_lecture: str | None, topic: str | None
) -> None:
    if lecture and sub_lecture and topic:
        render_chat(lecture, sub_lecture, topic)
        return

    crumbs = breadcrumb_html(lecture, sub_lecture, topic)
    if lecture and sub_lecture:
        number = lecture.split()[-1]
        ring = number
        heading = sub_lecture
        topic_options = TOPICS.get((lecture, sub_lecture), [])
        body = (
            "Pick Base Model, Fine-tuned Model, or RLHF-aligned Model to open that section."
            if topic_options
            else f"Content for {lecture} · {sub_lecture} will land here next."
        )
        pill = "Select a topic" if topic_options else sub_lecture
    elif lecture:
        number = lecture.split()[-1]
        subs = SUB_LECTURES.get(lecture, [])
        ring = number
        heading = f"{lecture} is selected"
        body = (
            "Pick Tokenisation, Input context, or Post Training to open that section."
            if subs
            else "Sub lectures are not wired yet for this lecture."
        )
        pill = "Select a sub lecture" if subs else "Sub lecture · coming soon"
    else:
        number = "—"
        ring = "AI"
        heading = "Welcome to the lecture workspace"
        body = "Choose a lecture from the side pane. Sub lectures appear when that lecture has them."
        pill = "Local preview"

    st.markdown(
        f"""
        <section class="lesson-block">
          <div class="lesson-block-header">
            <div class="lesson-number">{number}</div>
            {crumbs}
          </div>
          <div class="lesson-block-body">
            <div class="lesson-empty">
              <div class="lesson-empty-ring">{ring}</div>
              <p class="lesson-empty-title">{heading}</p>
              <p>{body}</p>
              <span class="lesson-pill">{pill}</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_crumbs(lecture, sub_lecture, topic)


st.set_page_config(
    page_title="AI Course",
    page_icon=str(FAVICON),
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

with st.sidebar:
    lecture = st.selectbox(
        "Lecture",
        options=LECTURES,
        index=None,
        placeholder="Select a lecture",
        accept_new_options=False,
        key="lecture_select",
    )
    if st.session_state.get("_last_lecture") != lecture:
        st.session_state.pop("sub_lecture_select", None)
        st.session_state.pop("topic_select", None)
        st.session_state._last_lecture = lecture
    sub_options = SUB_LECTURES.get(lecture or "", [])
    if sub_options:
        sub_lecture = st.selectbox(
            "Sub lecture",
            options=sub_options,
            index=None,
            placeholder="Select a sub lecture",
            accept_new_options=False,
            key="sub_lecture_select",
        )
    else:
        sub_lecture = None
        st.selectbox(
            "Sub lecture",
            options=["Coming soon"],
            index=0,
            disabled=True,
            accept_new_options=False,
            key="sub-disabled",
        )
    if st.session_state.get("_last_sub") != sub_lecture:
        st.session_state.pop("topic_select", None)
        st.session_state._last_sub = sub_lecture
    topic_options = TOPICS.get((lecture or "", sub_lecture or ""), [])
    if topic_options:
        topic = st.selectbox(
            "Topic",
            options=topic_options,
            index=None,
            placeholder="Select a topic",
            accept_new_options=False,
            key="topic_select",
        )
    else:
        topic = None

render_header()
render_workspace(lecture, sub_lecture, topic)
lock_dropdowns()
