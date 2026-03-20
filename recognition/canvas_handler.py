"""

Canvas handler for handwritten step input (Phase 1 MVP).

Renders a `streamlit-drawable-canvas` component and runs OCR on demand.
"""

from __future__ import annotations


import streamlit as st
from logger import get_logger

logger = get_logger()
from PIL import Image
import base64
import io
from typing import Any
import hashlib
import numpy as np

from recognition.ocr_processor import ocr_image_to_text


def _decode_canvas_image_data(image_data: Any) -> Image.Image | None:
    """
    `st_canvas` returns base64 PNG in `image_data` (often with a data URL prefix).
    """
    if image_data is None:
        return None

    if isinstance(image_data, np.ndarray):
        if image_data.size == 0:
            return None
        try:
            if image_data.dtype != np.uint8:
                image_data = image_data.astype(np.uint8)
            return Image.fromarray(image_data)
        except Exception:
            return None

    if not isinstance(image_data, str):
        return None

    if not image_data.strip():
        return None

    try:
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        raw = base64.b64decode(image_data)
        return Image.open(io.BytesIO(raw))
    except Exception:
        return None


def _hash_canvas_image_data(image_data: Any) -> str | None:
    if image_data is None:
        return None

    try:
        if isinstance(image_data, np.ndarray):
            if image_data.size == 0:
                return None
            return hashlib.sha1(image_data.tobytes()).hexdigest()

        if isinstance(image_data, str):
            data = image_data
            if "," in data:
                data = data.split(",", 1)[1]
            data = data.strip()
            if not data:
                return None
            return hashlib.sha1(data.encode("utf-8")).hexdigest()
    except Exception:
        return None

    return None


def get_latest_canvas_ocr(force_refresh: bool = False) -> str | None:
    image_data = st.session_state.get("latest_canvas_image_data")
    image_hash = _hash_canvas_image_data(image_data)
    if image_hash is None:
        logger.debug("Canvas OCR: no image data")
        return None

    ocr_cache = st.session_state.setdefault("canvas_ocr_cache", {})
    if not force_refresh and image_hash in ocr_cache:
        cached = ocr_cache[image_hash]
        logger.debug("Canvas OCR: returning cached result '%s'", cached or "(empty)")
        return cached or None

    image = _decode_canvas_image_data(image_data)
    if image is None:
        logger.warning("Canvas OCR: failed to decode image data")
        ocr_cache[image_hash] = ""
        return None

    logger.debug("Canvas OCR: processing image (hash=%s, force_refresh=%s)", image_hash[:8], force_refresh)
    text = (ocr_image_to_text(image) or "").strip()
    ocr_cache[image_hash] = text
    st.session_state.latest_canvas_ocr_text = text
    st.session_state.latest_canvas_hash = image_hash
    logger.info("Canvas OCR: result='%s'", text or "(empty)")
    return text or None


def render_canvas() -> tuple[bool, str | None]:
    """
    Render a streamlit drawable canvas and return
    `(interpret_clicked, ocr_candidate_text)`.
    Implemented in the OCR step.
    """
    try:
        from streamlit_drawable_canvas import st_canvas
    except Exception as e:
        logger.error("Canvas: streamlit-drawable-canvas not available: %s", repr(e))
        st.warning("Canvas input is unavailable (streamlit-drawable-canvas missing).")
        return False, None

    controls_col1, controls_col2 = st.columns([2, 2])
    with controls_col1:
        draw_tool = st.radio("Tool", ["Pen", "Eraser"], horizontal=True, key="canvas_tool")

    pen_color_map = {
        "Black": "#000000",
        "Red": "#FF0000",
        "Yellow": "#FFD700",
    }
    with controls_col2:
        pen_color_name = st.radio("Ink", list(pen_color_map.keys()), horizontal=True, key="canvas_ink_color")

    stroke_color = pen_color_map.get(pen_color_name, "#000000") if draw_tool == "Pen" else "#FFFFFF"
    stroke_width = 3 if draw_tool == "Pen" else 20

    canvas_result: Any = st_canvas(
        height=180,
        width=620,
        drawing_mode="freedraw",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#FFFFFF",
        key="math_tutor_canvas",
    )

    image_data = canvas_result.image_data if hasattr(canvas_result, "image_data") else None
    st.session_state.latest_canvas_image_data = image_data
    st.session_state.latest_canvas_hash = _hash_canvas_image_data(image_data)

    # Only run OCR when user clicks the button.
    recognize = st.button("Interpret", key="recognize_handwriting")
    if not recognize:
        return False, None

    logger.info("Canvas: Interpret button clicked")
    # Reuse cache for unchanged drawings to keep OCR responsive.
    result = get_latest_canvas_ocr(force_refresh=False)
    logger.info("Canvas: Interpret result=%s", repr(result) if result else "(none)")
    return True, result

