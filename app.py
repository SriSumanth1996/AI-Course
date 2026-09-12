from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st
from lectures import LECTURES, SUB_LECTURES, TOPICS, get_lecture

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STYLES = ROOT / "styles" / "app.css"
FAVICON = ASSETS / "favicon.svg"

BITSOM_LOGO = (
    "https://www.bitsom.edu.in/wp-content/uploads/2023/04/zero_scroll_logo-icn-1.svg"
)


def lecture_number(lecture: str | None) -> int | None:
    if not lecture:
        return None
    token = lecture.split()[-1]
    return int(token) if token.isdigit() else None


def header_host(lecture: str | None) -> str | None:
    number = lecture_number(lecture)
    if number is None:
        return None
    if 1 <= number <= 3:
        return "Dr. Meensakhi Balakrishna"
    if 4 <= number <= 10:
        return "Dr. Rachit Kamdar"
    return None


def header_greeting_html(lecture: str | None) -> str:
    host = header_host(lecture)
    if not host:
        return ""
    return (
        '<div class="lecture-header-cards">'
        '<div class="lecture-header-card">'
        f'<div class="lecture-header-greeting-hi">Hi {escape(host)}!</div>'
        '<div class="lecture-header-greeting-wish">Welcome to your teaching space</div>'
        "</div>"
        "</div>"
    )


def inject_css() -> None:
    css = STYLES.read_text(encoding="utf-8")
    st.html(
        "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500&display=swap'>"
        f"<style>{css}</style>"
        """
        <script>
        (function () {
          if (window.__lectureChrome === 32) return;
          window.__lectureChrome = 32;
          window.__crumbForward = true;
          window.__rlhfForward = true;

          function clickHidden(key) {
            if (!key) return false;
            var nodes = document.querySelectorAll('[class*="st-key-' + key + '"]');
            for (var i = 0; i < nodes.length; i++) {
              var node = nodes[i];
              var btn = node.tagName === "BUTTON" ? node : node.querySelector("button");
              if (btn) {
                btn.click();
                return true;
              }
            }
            if (key === "rlhf_ctrl_ok") {
              var submit = document.querySelector(
                '[class*="st-key-rlhf_ctrl_form"] button, [data-testid="stFormSubmitButton"] button'
              );
              if (submit) {
                submit.click();
                return true;
              }
            }
            return false;
          }

          function activePick(menu, kind) {
            var active = menu.querySelector('[data-rlhf-pick="' + kind + '"].is-active');
            if (active) return active.getAttribute("data-rlhf-value");
            var current = menu.querySelector('[data-rlhf-row="' + kind + '"] .rlhf-control-current');
            if (current) {
              var text = (current.textContent || "").trim();
              if (text) return text;
            }
            return "Auto";
          }

          function collectRlhfDraft(menu) {
            var draft = {
              output_length: activePick(menu, "tok"),
              reasoning: activePick(menu, "rsn"),
              verbosity: activePick(menu, "vrb"),
              temperature: null
            };
            var tempEnabled = menu.querySelector("[data-temp-enabled]");
            var tempVisible = !tempEnabled || tempEnabled.style.display !== "none";
            var manual = menu.querySelector('[data-rlhf-temp-mode="Manual"].is-active');
            var tempCurrent = menu.querySelector('[data-rlhf-row="tmp"] .rlhf-control-current');
            var tempLabel = tempCurrent ? (tempCurrent.textContent || "").trim() : "";
            if (tempVisible && manual) {
              var rangeEl = menu.querySelector("[data-rlhf-temp-range]");
              draft.temperature = rangeEl ? parseFloat(rangeEl.value) : 0.7;
            } else if (tempLabel && tempLabel !== "Auto" && tempLabel !== "Not supported") {
              var parsed = parseFloat(tempLabel);
              if (!isNaN(parsed)) draft.temperature = parsed;
            }
            return draft;
          }

          function writeRlhfDraft(draft) {
            var input = document.querySelector(
              '[class*="st-key-rlhf_controls_draft"] textarea, ' +
              '[class*="st-key-rlhf_controls_draft"] input'
            );
            if (!input) return false;
            var proto = input.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
            var setter = Object.getOwnPropertyDescriptor(proto, "value").set;
            setter.call(input, JSON.stringify(draft));
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            return true;
          }

          var allow = { ArrowDown: 1, ArrowUp: 1, Enter: 1, Escape: 1, Tab: 1, Home: 1, End: 1 };

          function lockInput(el) {
            el.setAttribute("readonly", "readonly");
            el.setAttribute("inputmode", "none");
            el.setAttribute("autocomplete", "off");
            el.style.caretColor = "transparent";
            if (el.dataset.dropdownLocked === "1") return;
            el.dataset.dropdownLocked = "1";
            function block(e) {
              if (e.type === "keydown" && allow[e.key]) return;
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
              var svgs = select.querySelectorAll("svg");
              var chevron = null;
              svgs.forEach(function (svg) {
                var path = svg.querySelector("path");
                var d = path ? path.getAttribute("d") || "" : "";
                if (d.indexOf("M12 2C6.47") === -1) chevron = svg;
              });
              if (!chevron && svgs.length) chevron = svgs[svgs.length - 1];
              if (!chevron) return;
              var host = chevron.closest("button") || chevron.parentElement;
              ["mousedown", "mouseup", "click"].forEach(function (type) {
                host.dispatchEvent(new window.MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
              });
            });
          }

          function fitChatInput(el) {
            if (el.dataset.fitting === "1") return;
            el.dataset.fitting = "1";
            el.style.setProperty("padding", "0px", "important");
            el.style.setProperty("color", "#111111", "important");
            el.style.setProperty("-webkit-text-fill-color", "#111111", "important");
            el.style.setProperty("caret-color", "#111111", "important");
            el.style.setProperty("height", "auto", "important");
            var next = el.value ? Math.min(Math.max(el.scrollHeight, 22), 88) : 22;
            el.style.setProperty("height", next + "px", "important");
            el.style.setProperty("overflow-y", next >= 88 ? "auto" : "hidden", "important");
            if (next < 88) el.scrollTop = 0;
            requestAnimationFrame(function () {
              el.dataset.fitting = "0";
            });
          }

          function wireChatInput(el) {
            if (el.dataset.chatFit === "1") return;
            el.dataset.chatFit = "1";
            ["input", "keyup", "keydown", "change", "paste"].forEach(function (type) {
              el.addEventListener(type, function () {
                fitChatInput(el);
                requestAnimationFrame(function () { fitChatInput(el); });
              });
            });
            fitChatInput(el);
          }

          function pinThread(el) {
            if (!el.dataset.chatScrollWired) {
              el.dataset.chatScrollWired = "1";
              el.dataset.stickBottom = "1";
              el.addEventListener("scroll", function () {
                var gap = el.scrollHeight - el.scrollTop - el.clientHeight;
                el.dataset.stickBottom = gap < 80 ? "1" : "0";
              }, { passive: true });
            }
            if (el.dataset.stickBottom !== "0") {
              el.scrollTop = el.scrollHeight;
            }
          }

          var fileHint = "Accepts Word, PDF or text only";
          var fileReject = "Only Word, PDF or text files are accepted.";

          function hintFileUi() {
            document.querySelectorAll('[data-testid="stChatInputFileUploadButton"]').forEach(function (btn) {
              btn.setAttribute("aria-label", fileHint);
            });
            document.querySelectorAll('[data-testid="stTooltipContent"]').forEach(function (el) {
              var text = el.textContent || "";
              if (/Upload or drag|drag and drop|Accepts Word, PDF or text only/i.test(text)) {
                el.textContent = fileHint;
                if (el.parentElement) el.parentElement.style.display = "none";
              }
            });
            document.querySelectorAll('[data-testid="stTooltipErrorContent"]').forEach(function (el) {
              var text = el.textContent || "";
              if (/not allowed/i.test(text)) el.textContent = fileReject;
            });
            document.querySelectorAll('[data-testid="stFileChip"] [role="alert"]').forEach(function (el) {
              var text = el.textContent || "";
              if (/not allowed/i.test(text)) el.textContent = "Error: " + fileReject;
            });
          }

          function wireTempRange() {
            document.querySelectorAll("[data-rlhf-temp-range]").forEach(function (el) {
              if (el.dataset.tempWired === "1") return;
              el.dataset.tempWired = "1";
              el.addEventListener("input", function () {
                var value = parseFloat(el.value).toFixed(1);
                var readout = el.parentElement && el.parentElement.querySelector(".rlhf-temp-readout");
                if (readout) readout.textContent = value;
                var fly = el.closest(".rlhf-control-flyout");
                var label = fly && fly.querySelector(".rlhf-control-current");
                if (label) label.textContent = value;
              });
            });
          }

          function scan() {
            document.querySelectorAll('[data-testid="stSelectbox"] input, [data-baseweb="select"] input').forEach(lockInput);
            document.querySelectorAll('[data-baseweb="select"]').forEach(wireOpenOnClick);
            document.querySelectorAll('[data-testid="stChatInput"] textarea, [data-testid="stChatInputTextArea"]').forEach(wireChatInput);
            document.querySelectorAll(".model-chat-thread").forEach(pinThread);
            hintFileUi();
            wireTempRange();
          }

          document.addEventListener("click", function (e) {
            var crumb = e.target.closest(".crumb-link");
            if (crumb) {
              e.preventDefault();
              clickHidden("crumb_" + (crumb.getAttribute("data-level") || "lecture"));
              return;
            }
            if (e.target.closest(".rlhf-bar.is-locked")) {
              e.preventDefault();
              return;
            }
            var companyOpt = e.target.closest("[data-rlhf-company]");
            if (companyOpt) {
              e.preventDefault();
              clickHidden("rlhf_co_" + companyOpt.getAttribute("data-rlhf-company"));
              return;
            }
            var modeOpt = e.target.closest("[data-rlhf-mode]");
            if (modeOpt) {
              e.preventDefault();
              clickHidden("rlhf_mode_" + modeOpt.getAttribute("data-rlhf-mode"));
              return;
            }
            var modelOpt = e.target.closest("[data-rlhf-model]");
            if (modelOpt) {
              e.preventDefault();
              clickHidden("rlhf_md_" + modelOpt.getAttribute("data-rlhf-model"));
              return;
            }
            var pickOpt = e.target.closest("[data-rlhf-pick]");
            if (pickOpt) {
              e.preventDefault();
              var menu = pickOpt.closest(".rlhf-dd-menu");
              var kind = pickOpt.getAttribute("data-rlhf-pick") || "";
              var value = pickOpt.getAttribute("data-rlhf-value") || "";
              if (menu) {
                menu.querySelectorAll('[data-rlhf-pick="' + kind + '"]').forEach(function (item) {
                  item.classList.toggle("is-active", item.getAttribute("data-rlhf-value") === value);
                });
                var current = menu.querySelector('[data-rlhf-row="' + kind + '"] .rlhf-control-current');
                if (current) current.textContent = value;
                var block = menu.querySelector("[data-temp-policy='reasoning_none']");
                if (block && kind === "rsn") {
                  var on = value === "None";
                  var enabled = block.querySelector("[data-temp-enabled]");
                  var locked = block.querySelector("[data-temp-locked]");
                  if (enabled) enabled.style.display = on ? "block" : "none";
                  if (locked) locked.style.display = on ? "none" : "block";
                }
              }
              return;
            }
            var tempMode = e.target.closest("[data-rlhf-temp-mode]");
            if (tempMode) {
              e.preventDefault();
              var tempCard = tempMode.closest(".rlhf-length-card");
              var mode = tempMode.getAttribute("data-rlhf-temp-mode") || "Auto";
              if (tempCard) {
                tempCard.querySelectorAll("[data-rlhf-temp-mode]").forEach(function (item) {
                  item.classList.toggle("is-active", item === tempMode);
                });
                var slider = tempCard.querySelector(".rlhf-temp-slider");
                if (slider) slider.classList.toggle("is-hidden", mode !== "Manual");
                var rowCur = tempMode.closest(".rlhf-control-flyout");
                var label = rowCur && rowCur.querySelector(".rlhf-control-current");
                if (label) {
                  if (mode === "Auto") label.textContent = "Auto";
                  else {
                    var range = tempCard.querySelector("[data-rlhf-temp-range]");
                    label.textContent = range ? parseFloat(range.value).toFixed(1) : "0.7";
                  }
                }
              }
              return;
            }
            var okCtrl = e.target.closest("[data-rlhf-ctrl-ok]");
            if (okCtrl) {
              e.preventDefault();
              var okMenu = okCtrl.closest(".rlhf-dd-menu");
              if (okMenu) {
                writeRlhfDraft(collectRlhfDraft(okMenu));
                setTimeout(function () {
                  clickHidden("rlhf_ctrl_ok");
                }, 80);
                setTimeout(function () {
                  clickHidden("rlhf_ctrl_ok");
                }, 220);
              }
              return;
            }
            var flyToggle = e.target.closest("summary.rlhf-control-row");
            if (flyToggle) {
              var fly = flyToggle.closest(".rlhf-control-flyout");
              document.querySelectorAll(".rlhf-control-flyout").forEach(function (el) {
                if (el !== fly) el.removeAttribute("open");
              });
              return;
            }
            var clearChat = e.target.closest("[data-rlhf-clear], [data-llama-clear]");
            if (clearChat) {
              e.preventDefault();
              clickHidden(clearChat.hasAttribute("data-llama-clear") ? "llama_clear" : "rlhf_clear");
              return;
            }
            var topToggle = e.target.closest("summary.rlhf-dd-toggle");
            if (topToggle) {
              var host = topToggle.closest(".rlhf-dd");
              document.querySelectorAll(".rlhf-dd").forEach(function (el) {
                if (el !== host) el.removeAttribute("open");
              });
              return;
            }
            if (!e.target.closest(".rlhf-dd")) {
              document.querySelectorAll(".rlhf-dd, .rlhf-control-flyout").forEach(function (el) {
                el.removeAttribute("open");
              });
            }
          }, true);

          ["input", "keyup", "paste"].forEach(function (type) {
            document.addEventListener(type, function (e) {
              var el = e.target && e.target.closest && e.target.closest(
                '[data-testid="stChatInput"] textarea, [data-testid="stChatInputTextArea"]'
              );
              if (el) {
                fitChatInput(el);
                requestAnimationFrame(function () { fitChatInput(el); });
              }
            }, true);
          });

          scan();
          new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
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


def render_header(lecture: str | None = None) -> None:
    greet_html = header_greeting_html(lecture)
    st.markdown(
        f"""
        <header class="lecture-header">
          <div class="lecture-header-inner">
            <div class="lecture-header-logo">
              <img src="{BITSOM_LOGO}" alt="BITSoM Logo" />
            </div>
            <div class="lecture-header-text">
              <span class="lecture-header-title">Foundations of AI</span>
              <span class="lecture-header-sub">AI Course</span>
            </div>
            {greet_html}
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_workspace(
    lecture: str | None, sub_lecture: str | None, topic: str | None
) -> None:
    chapter = get_lecture(lecture)
    render_fn = getattr(chapter, "render", None) if chapter else None
    if lecture and sub_lecture and topic and callable(render_fn):
        render_fn(
            lecture,
            sub_lecture,
            topic,
            crumbs=breadcrumb_html(lecture, sub_lecture, topic),
        )
        render_crumbs(lecture, sub_lecture, topic)
        return

    crumbs = breadcrumb_html(lecture, sub_lecture, topic)
    if lecture and sub_lecture:
        number = lecture.split()[-1]
        ring = number
        heading = sub_lecture
        topic_options = TOPICS.get((lecture, sub_lecture), [])
        pick_topic = getattr(chapter, "PICK_TOPIC", "") if chapter else ""
        body = (
            pick_topic
            if topic_options and pick_topic
            else f"Content for {lecture} · {sub_lecture} will land here next."
        )
        pill = "Select a topic" if topic_options else sub_lecture
    elif lecture:
        number = lecture.split()[-1]
        subs = SUB_LECTURES.get(lecture, [])
        ring = number
        heading = f"{lecture} is selected"
        pick_sub = getattr(chapter, "PICK_SUB", "") if chapter else ""
        body = (
            pick_sub
            if subs and pick_sub
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
    page_title="Foundations of AI",
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

render_header(lecture)
render_workspace(lecture, sub_lecture, topic)
