from __future__ import annotations

import copy

import streamlit as st

TITLE = "Lecture 3"
SUB_LECTURES = ["Neural Networks", "Confusion Matrix"]
TOPICS = {
    "Neural Networks": ["Neural Networks"],
    "Confusion Matrix": ["Confusion Matrix"],
}
PICK_SUB = "Pick Neural Networks or Confusion Matrix to open that section."
PICK_TOPIC = "Pick Neural Networks to open that section."
PICK_TOPIC_BY_SUB = {
    "Neural Networks": PICK_TOPIC,
    "Confusion Matrix": "Pick Confusion Matrix to open that section.",
}

TOPIC_NAME = "Neural Networks"
CONFUSION_TOPIC = "Confusion Matrix"

CANVAS_SIZE = 220
NEURON_GALLERY_K = 8
NEURON_GALLERY_COLS = 4
NEURON_GRID_COLS = 8
NEURON_INACTIVE_MAX = 0.01
TOP_K = 6

EMPTY_CANVAS = {"version": "4.4.0", "objects": []}


def render(
    lecture: str | None,
    sub_lecture: str | None,
    topic: str,
    *,
    crumbs: str,
) -> None:
    from html import escape

    number = (lecture or "3").split()[-1]
    header = (
        "<div class='lesson-block-header'>"
        f"<div class='lesson-number'>{escape(number)}</div>"
        f"{crumbs}"
        "</div>"
    )
    with st.container(key="lesson_block", gap=None):
        st.html(header)
        if topic == CONFUSION_TOPIC:
            with st.container(key="cm_body"):
                tab_problem, tab_drag = st.tabs(["Exercise", "Drag the threshold"])
                with tab_problem:
                    _render_confusion_problem()
                with tab_drag:
                    from services.confusion_matrix import render as render_confusion

                    render_confusion()
            return
        if topic != TOPIC_NAME:
            return
        with st.container(key="nn_body"):
            tab_exercise, tab_label, tab_draw = st.tabs(
                ["Exercise", "Label the neuron", "Draw a character"]
            )
            with tab_exercise:
                _render_exercise()
            with tab_label:
                with st.container(key="nn_label"):
                    _render_label()
            with tab_draw:
                _render_draw()


def _render_confusion_problem() -> None:
    st.html(
        """
        <section class="cmx-card" aria-labelledby="cm-problem-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise</div>
          <h2 id="cm-problem-title">A high score can still hide mistakes</h2>
          <div class="cmx-steps">
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">1</span>
                <h3>A rare disease,<br>one threshold</h3>
                <span class="cmx-icon cmx-icon-people"></span>
              </div>
              <ul class="cmx-points">
                <li>Forty patients. A few are actually sick. A screening test gives each person a risk score from 0 to 1.</li>
                <li>Anyone at or above the decision threshold is predicted sick. Everyone below it is predicted not sick.</li>
                <li>Moving that one line changes who is predicted sick and who is predicted not sick.</li>
              </ul>
            </article>
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">2</span>
                <h3>Four kinds of result</h3>
                <span class="cmx-icon cmx-icon-result"></span>
              </div>
              <ul class="cmx-points">
                <li><strong>True positive</strong> &mdash; actually sick, and predicted sick.</li>
                <li><strong>False negative</strong> &mdash; actually sick, but predicted not sick.</li>
                <li><strong>False positive</strong> &mdash; actually not sick, but predicted sick.</li>
                <li><strong>True negative</strong> &mdash; actually not sick, and predicted not sick.</li>
              </ul>
            </article>
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">3</span>
                <h3>Why one percentage<br>is not enough</h3>
                <span class="cmx-icon cmx-icon-bars"></span>
              </div>
              <ul class="cmx-points">
                <li><strong>Accuracy</strong> counts every correct box. With few sick patients, predicting the healthy ones as not sick can make accuracy look strong.</li>
                <li><strong>Precision</strong> asks: of everyone predicted sick, how many are actually sick?</li>
                <li><strong>Recall</strong> asks: of everyone actually sick, how many were predicted sick?</li>
              </ul>
            </article>
          </div>
          <div class="cmx-next">
            <span class="cmx-arrow"></span>
            <span class="cmx-sep"></span>
            <span><strong>Next</strong> &mdash; Open <strong>Drag the threshold.</strong> Drag the gold line and watch those four boxes change.</span>
          </div>
        </section>
        """
    )


def _render_exercise() -> None:
    st.html(
        """
        <section class="cmx-card" aria-labelledby="nn-exercise-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise</div>
          <h2 id="nn-exercise-title">Discover what a neuron detects</h2>
          <div class="cmx-steps">
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">1</span>
                <h3>Study a neuron</h3>
                <span class="cmx-icon cmx-icon-neurons"></span>
              </div>
              <ul class="cmx-points">
                <li>Open <strong>Label the neuron</strong> and select any navy neuron &mdash; the selected neuron turns gold.</li>
                <li>Examine its eight strongest examples. Ignore the letter labels and identify the shared visual pattern, such as a diagonal, loop, curve, or crossbar.</li>
                <li>Form a hypothesis &mdash; &ldquo;Neuron 02 detects loops.&rdquo;</li>
              </ul>
            </article>
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">2</span>
                <h3>Test your idea</h3>
                <span class="cmx-icon cmx-icon-pen"></span>
              </div>
              <ul class="cmx-points">
                <li>Remember the neuron number and open <strong>Draw a character</strong>.</li>
                <li>Clearly recreate the common visual pattern you identified.</li>
                <li>Focus on the pattern rather than copying a particular letter. The activation grid shows how strongly each of the 24 neurons responds.</li>
              </ul>
            </article>
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">3</span>
                <h3>Check the result</h3>
                <span class="cmx-icon cmx-icon-activation"></span>
              </div>
              <ul class="cmx-points">
                <li>Find the neuron number you studied in the activation grid.</li>
                <li>A <strong>brighter</strong> neuron indicates a stronger response; a <strong>dark</strong> neuron indicates a weak or absent response.</li>
                <li>If your neuron lights up, the result supports your hypothesis. If it remains dark, try a clearer variation before reconsidering what the neuron detects.</li>
              </ul>
            </article>
          </div>
          <div class="cmx-next">
            <span class="cmx-arrow"></span>
            <span class="cmx-sep"></span>
            <span><strong>Remember</strong> &mdash; Note the neuron number before switching tabs. It will not be highlighted automatically in the activation grid.</span>
          </div>
        </section>
        """
    )


def _model():
    from services.neural_interpretability import CHECKPOINT_PATH
    from services.neural_interpretability import load_model

    if not CHECKPOINT_PATH.is_file():
        st.error("The Neural Networks model file is not in the project yet.")
        st.stop()
    if "nn_model" not in st.session_state:
        st.session_state["nn_model"] = load_model()
    return st.session_state["nn_model"]


def _bank():
    from services.neural_interpretability import BANK_PATH
    from services.neural_interpretability import load_bank

    if not BANK_PATH.is_file():
        st.error("The neuron examples are not in the project yet.")
        st.stop()
    if "nn_bank" not in st.session_state:
        st.session_state["nn_bank"] = load_bank()
    return st.session_state["nn_bank"]


def _render_label() -> None:
    import numpy as np

    from services.neural_interpretability import plot_top_firing_examples
    from services.neural_interpretability import top_firing_examples

    st.write(
        "Pick a latent cell. The pictures are the handwritten characters that turn that cell on most strongly."
    )
    model = _model()
    bank = _bank()
    latent_dim = model.config.latent_dim
    st.session_state.setdefault("nn_selected_neuron", 0)
    selected = int(st.session_state["nn_selected_neuron"])
    if selected < 0 or selected >= latent_dim:
        selected = 0
        st.session_state["nn_selected_neuron"] = 0

    neuron_max = np.max(bank.latents, axis=0)
    active_mask = neuron_max >= NEURON_INACTIVE_MAX
    if not np.any(active_mask):
        st.warning("No active neurons in the saved examples.")
        return
    if not active_mask[selected]:
        selected = int(np.where(active_mask)[0][0])
        st.session_state["nn_selected_neuron"] = selected

    pick_col, gallery_col = st.columns(
        [0.78, 1.22], gap="large", vertical_alignment="center"
    )
    with pick_col:
        with st.container(key="nn_neuron_picker", border=True):
            st.html('<div class="nn-picker-title">Select a neuron</div>')
            with st.container(key="nn_neurons"):
                _neuron_grid(latent_dim, active_mask, selected)
    with gallery_col:
        with st.container(key="nn_gallery"):
            st.html(
                f'<h3 class="nn-gallery-title">Neuron {selected:02d}</h3>'
            )
            examples = top_firing_examples(bank, selected, top_k=NEURON_GALLERY_K)
            st.pyplot(
                plot_top_firing_examples(
                    examples,
                    neuron_idx=selected,
                    cols_per_row=NEURON_GALLERY_COLS,
                ),
                clear_figure=True,
                width="content",
            )


def _neuron_grid(latent_dim: int, active_mask, selected: int) -> None:
    for row in range((latent_dim + NEURON_GRID_COLS - 1) // NEURON_GRID_COLS):
        cols = st.columns(NEURON_GRID_COLS, gap="small")
        for col_idx in range(NEURON_GRID_COLS):
            neuron_idx = row * NEURON_GRID_COLS + col_idx
            if neuron_idx >= latent_dim:
                break
            with cols[col_idx]:
                label = f"{neuron_idx:02d}"
                if active_mask[neuron_idx]:
                    if st.button(
                        label,
                        key=f"nn_neuron_{neuron_idx}",
                        type="primary" if neuron_idx == selected else "secondary",
                        width="stretch",
                    ):
                        st.session_state["nn_selected_neuron"] = neuron_idx
                        st.rerun()
                else:
                    st.button(
                        label,
                        key=f"nn_neuron_dead_{neuron_idx}",
                        disabled=True,
                        width="stretch",
                    )


def _shift_2d_zeros(image, *, dy: int, dx: int):
    import numpy as np

    height, width = image.shape
    out = np.zeros((height, width), dtype=np.float32)
    src_y0 = max(0, -dy)
    src_y1 = min(height, height - dy)
    src_x0 = max(0, -dx)
    src_x1 = min(width, width - dx)
    dst_y0 = max(0, dy)
    dst_x0 = max(0, dx)
    if src_y1 <= src_y0 or src_x1 <= src_x0:
        return out
    dst_y1 = dst_y0 + (src_y1 - src_y0)
    dst_x1 = dst_x0 + (src_x1 - src_x0)
    out[dst_y0:dst_y1, dst_x0:dst_x1] = image[src_y0:src_y1, src_x0:src_x1]
    return out


def _normalize_ink(ink):
    import numpy as np
    from PIL import Image
    values = np.asarray(ink, dtype=np.float32)
    if values.max() < 0.05:
        return None
    mask = values >= 0.10
    if not np.any(mask):
        return None
    ys, xs = np.where(mask)
    cropped = values[int(ys.min()) : int(ys.max()) + 1, int(xs.min()) : int(xs.max()) + 1]
    if cropped.size == 0 or cropped.max() < 0.05:
        return None
    pil = Image.fromarray((cropped * 255).astype(np.uint8), mode="L")
    width, height = pil.size
    scale = 20 / float(max(width, height))
    new_w = max(1, int(round(width * scale)))
    new_h = max(1, int(round(height * scale)))
    pil = pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
    frame = Image.new("L", (28, 28), color=0)
    frame.paste(pil, ((28 - new_w) // 2, (28 - new_h) // 2))
    arr = np.asarray(frame, dtype=np.float32) / 255.0
    total = float(arr.sum())
    if total <= 1e-6:
        return None
    ys_f = np.arange(28, dtype=np.float32)
    xs_f = np.arange(28, dtype=np.float32)
    cy = float((arr.sum(axis=1) * ys_f).sum() / total)
    cx = float((arr.sum(axis=0) * xs_f).sum() / total)
    center = 13.5
    dy = int(round(center - cy))
    dx = int(round(center - cx))
    if dy or dx:
        arr = _shift_2d_zeros(arr, dy=dy, dx=dx)
    return arr


def _canvas_to_vector(image_data):
    import numpy as np
    import torch
    from PIL import Image

    if image_data is None:
        return None
    rgba = np.asarray(Image.fromarray(image_data.astype("uint8"), "RGBA").convert("RGBA"))
    ink = np.clip(rgba[:, :, :3].mean(axis=2) / 255.0, 0.0, 1.0)
    arr = _normalize_ink(ink)
    if arr is None:
        return None
    return torch.from_numpy(arr.reshape(-1))


def _encode(model, vector):
    import torch

    from services.neural_interpretability import tensor_to_image

    with torch.no_grad():
        recon, latent = model(vector.float().view(1, -1))
    return (
        vector.numpy().reshape(28, 28),
        tensor_to_image(recon[0]),
        latent[0].detach().cpu().numpy(),
    )


def _init_draw_canvas() -> None:
    version = "nn-draw-v2"
    if st.session_state.get("nn_draw_version") != version:
        st.session_state["nn_draw_version"] = version
        st.session_state["nn_canvas_version"] = 1
        st.session_state["nn_canvas_state"] = copy.deepcopy(EMPTY_CANVAS)
        st.session_state["nn_draw_result"] = None
    st.session_state.setdefault("nn_canvas_version", 1)
    st.session_state.setdefault("nn_canvas_state", copy.deepcopy(EMPTY_CANVAS))
    st.session_state.setdefault("nn_draw_result", None)


def _render_draw() -> None:
    _init_draw_canvas()
    model = _model()
    with st.container(key="nn_draw"):
        _render_draw_body(model)


def _render_draw_body(model) -> None:
    from streamlit_drawable_canvas import st_canvas

    from services.neural_interpretability import plot_latent_grid
    from services.neural_interpretability import plot_single_digit
    from services.neural_interpretability import top_active_neurons

    st.write(
        "Draw one character to see the cleaned input, its reconstruction, and the latent cells it activates."
    )

    clear_col, _ = st.columns([1, 5])
    if clear_col.button("Clear canvas", key="nn_clear_canvas"):
        st.session_state["nn_canvas_state"] = copy.deepcopy(EMPTY_CANVAS)
        st.session_state["nn_canvas_version"] += 1
        st.session_state["nn_draw_result"] = None
        st.rerun()

    canvas_col, image_col, reconstruction_col, latent_col = st.columns(
        [1, 1, 1, 1.45], gap="large", vertical_alignment="top"
    )
    with canvas_col:
        st.html('<div class="nn-panel-title nn-canvas-title">Canvas</div>')
        canvas = st_canvas(
            fill_color="#000000",
            stroke_width=10,
            stroke_color="#FFFFFF",
            background_color="#000000",
            height=CANVAS_SIZE,
            width=CANVAS_SIZE,
            drawing_mode="freedraw",
            update_streamlit=True,
            initial_drawing=copy.deepcopy(st.session_state["nn_canvas_state"]),
            display_toolbar=True,
            key=f"nn_canvas_{st.session_state['nn_canvas_version']}",
        )

    vector = _canvas_to_vector(canvas.image_data)
    if vector is not None:
        drawn, recon, latent = _encode(model, vector)
        result = {"input": drawn, "output": recon, "latent": latent}
        st.session_state["nn_draw_result"] = result
    else:
        result = st.session_state.get("nn_draw_result")

    with image_col:
        st.html('<div class="nn-panel-title">Your drawing</div>')
        if result is None:
            st.html(
                '<div class="nn-preview-placeholder nn-preview-square" '
                'role="img" aria-label="Your drawing preview is empty"></div>'
            )
        else:
            st.pyplot(
                plot_single_digit(result["input"]),
                clear_figure=True,
                width="content",
            )

    with reconstruction_col:
        st.html('<div class="nn-panel-title">Model reconstruction</div>')
        if result is None:
            st.html(
                '<div class="nn-preview-placeholder nn-preview-square" '
                'role="img" aria-label="Model reconstruction preview is empty"></div>'
            )
        else:
            st.pyplot(
                plot_single_digit(result["output"]),
                clear_figure=True,
                width="content",
            )

    with latent_col:
        st.html('<div class="nn-panel-title">Activated latent cells</div>')
        if result is None:
            st.html(
                '<div class="nn-preview-placeholder nn-preview-latent" '
                'role="img" aria-label="Activated latent cells preview is empty"></div>'
            )
        else:
            st.pyplot(
                plot_latent_grid(result["latent"]),
                clear_figure=True,
                width="content",
            )
            leaders = top_active_neurons(result["latent"], top_k=TOP_K)
            chips = "".join(
                '<div class="nn-active-chip">'
                f'<span class="nn-active-rank">{rank}</span>'
                f'<span class="nn-active-name">Neuron {idx:02d}</span>'
                f'<strong>{value:.2f}</strong>'
                "</div>"
                for rank, (idx, value) in enumerate(leaders, start=1)
            )
            st.html(
                '<div class="nn-active-summary">'
                '<div class="nn-active-title">Most active neurons</div>'
                f'<div class="nn-active-chips">{chips}</div>'
                "</div>"
            )
