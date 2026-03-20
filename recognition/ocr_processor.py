"""
OCR processing for handwriting-to-math (Phase 1 MVP).

This is intentionally conservative: if OCR quality is poor, we return an empty
string so the app can fall back to the user’s typed input.
"""

from __future__ import annotations


import re
from typing import Any
from logger import get_logger

logger = get_logger()


def _clean_ocr_text(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    # Normalize some common OCR artifacts.
    text = text.replace("−", "-").replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("×", "*").replace("·", "*")
    text = text.replace("÷", "/")
    text = text.replace("＝", "=")
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("pi", "pi")

    # Common OCR confusions in math contexts.
    # O → 0: Replace O with 0 when it appears:
    #   - between digits (e.g., 2O3 → 203)
    #   - after operators/delimiters (e.g., x-O → x-0, =O → =0, (O → (0)
    #   - at the start of the string (e.g., O=5 → 0=5)
    text = re.sub(r"(?<=\d)[Oo](?=\d)", "0", text)  # between digits
    text = re.sub(r"([=+\-*/(^\s])[Oo]", r"\g<1>0", text)  # after operators/delimiters
    text = re.sub(r"^[Oo](?=\d|=)", "0", text)  # at start followed by digit or =
    
    # l/I → 1: Replace l or I with 1 when between digits
    text = re.sub(r"(?<=\d)[lI](?=\d)", "1", text)

    # Keep only characters likely to be part of a math expression.
    # This is a whitelist; anything else is removed.
    text = re.sub(r"[^0-9a-zA-Z+\-*/^().=,\s]", "", text)

    # Standardize variable name variants often produced by OCR.
    text = re.sub(r"\bX\b", "x", text)
    text = re.sub(r"\bY\b", "y", text)

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_math_expression(ocr_text: str) -> str:
    """
    Convert raw OCR output into a single-line math candidate.
    """
    cleaned = _clean_ocr_text(ocr_text)
    # Heuristic: require at least one digit or common variable.
    if not re.search(r"(\d|x|y|pi|sin|cos|tan)", cleaned, flags=re.IGNORECASE):
        return ""
    return cleaned


def ocr_image_to_text(image: Any) -> str:
    """
    Run OCR on an image and return extracted math text.

    Expected input: PIL Image or numpy array-like.
    """
    logger.debug("OCR: starting on image (type=%s)", type(image).__name__)
    try:
        import numpy as np
        import cv2
        import pytesseract
        from PIL import Image
    except Exception:
        # If tesseract/OpenCV aren't configured, fail safely.
        return ""

    try:
        if isinstance(image, Image.Image):
            pil_img = image.convert("RGBA")
            white_bg = Image.new("RGBA", pil_img.size, (255, 255, 255, 255))
            img = np.array(Image.alpha_composite(white_bg, pil_img).convert("RGB"))
        else:
            img = np.array(image)

        if img.ndim == 3 and img.shape[-1] == 4:
            alpha = img[..., 3:4].astype("float32") / 255.0
            rgb = img[..., :3].astype("float32")
            img = (rgb * alpha + 255.0 * (1.0 - alpha)).clip(0, 255).astype("uint8")

        if img.ndim == 2:
            gray = img.astype("uint8")
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Preprocess for better recognition.
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Crop to the handwritten region if possible.
        non_white = cv2.findNonZero(255 - th)
        if non_white is not None:
            x, y, w, h = cv2.boundingRect(non_white)
            pad = 12
            x0 = max(x - pad, 0)
            y0 = max(y - pad, 0)
            x1 = min(x + w + pad, th.shape[1])
            y1 = min(y + h + pad, th.shape[0])
            th = th[y0:y1, x0:x1]
        else:
            logger.info("OCR: blank canvas region detected")
            return ""

        ink_pixels = int(np.count_nonzero(255 - th))
        if ink_pixels < 30:
            logger.info("OCR: too little ink detected (pixels=%d)", ink_pixels)
            return ""

        scale = 2
        th = cv2.resize(th, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        th_inv = 255 - th

        kernel = np.ones((2, 2), np.uint8)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=1)
        th_inv = cv2.morphologyEx(th_inv, cv2.MORPH_CLOSE, kernel, iterations=1)

        primary_config = "--psm 7 -c tessedit_char_whitelist=0123456789xyXYabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/^().=,|"
        fallback_configs = [
            "--psm 13 -c tessedit_char_whitelist=0123456789xyXYabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/^().=,|",
            "--psm 6 -c tessedit_char_whitelist=0123456789xyXYabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/^().=,|",
        ]

        candidates: list[str] = []

        def _run_ocr(img_processed: Any, cfg: str) -> str:
            try:
                return pytesseract.image_to_string(img_processed, config=cfg, timeout=2)
            except RuntimeError:
                logger.warning("OCR: pytesseract timeout for config=%s", cfg)
                return ""

        # Fast path: one common config on non-inverted image.
        raw_primary = _run_ocr(th, primary_config)
        candidate_primary = extract_math_expression(raw_primary)
        if candidate_primary:
            candidates.append(candidate_primary)
            if "=" in candidate_primary or len(candidate_primary) >= 5:
                logger.info("OCR: fast-path hit '%s'", candidate_primary)
                return candidate_primary

        # Fallback path: inverted image + alternate configs, early-return on strong candidate.
        for processed in (th_inv, th):
            for config in fallback_configs:
                raw = _run_ocr(processed, config)
                candidate = extract_math_expression(raw)
                if candidate and candidate not in candidates:
                    candidates.append(candidate)
                if candidate and ("=" in candidate or len(candidate) >= 5):
                    logger.info("OCR: fallback early-hit '%s'", candidate)
                    return candidate

        if not candidates:
            logger.info("OCR: no valid candidates recognized")
            return ""

        candidates.sort(key=lambda text: ("=" in text, len(text)), reverse=True)
        result = candidates[0]
        logger.info("OCR: recognized '%s' (candidates: %s)", result, candidates[:3])
        return result
    except Exception as e:
        # OCR failed at runtime (bad image/input/environment); fail safely.
        logger.error("OCR: runtime exception: %s", repr(e), exc_info=True)
        return ""


