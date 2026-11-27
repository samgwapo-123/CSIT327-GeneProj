"""Read text from prescription photos with RapidOCR (ONNX Runtime).

The OCR models ship inside the ``rapidocr`` wheel, so there is no external
Tesseract binary to install. Loading the three ONNX models takes a few seconds,
so the engine is built once per process and reused for every later upload.

Every failure path returns an empty string instead of raising: a blurry photo
must ask the user for a clearer one, not crash the scan page.
"""

import importlib.util
import logging
import os
import threading

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

_engine = None
_engine_error = None
_engine_lock = threading.Lock()


def _quiet_rapidocr():
    """RapidOCR configures an INFO logger with its own handler at import time.

    Only errors are worth showing: an empty detection result is already handled
    by returning an empty string, and the caller logs anything actionable.
    """
    for name in ("RapidOCR", "rapidocr"):
        package_logger = logging.getLogger(name)
        package_logger.setLevel(logging.ERROR)
        for handler in package_logger.handlers:
            handler.setLevel(logging.ERROR)


def _readable_image(image_path):
    """Cheap check before the models load: is this actually an image?"""
    try:
        with Image.open(image_path) as image:
            image.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def _get_engine():
    """Build the OCR engine on first use and reuse it afterwards."""
    global _engine, _engine_error

    if _engine is not None or _engine_error is not None:
        return _engine

    with _engine_lock:
        # Another request may have built it while this one waited for the lock.
        if _engine is not None or _engine_error is not None:
            return _engine

        try:
            _quiet_rapidocr()

            from rapidocr import RapidOCR

            _engine = RapidOCR()
            _quiet_rapidocr()
        except Exception as exc:  # pragma: no cover - depends on local install
            _engine_error = exc
            logger.warning("OCR engine could not start: %s", exc)
            return None

    return _engine


def ocr_available():
    """True when the OCR engine can be loaded in this environment."""
    return _get_engine() is not None


def ocr_installed():
    """Cheap check for the template: is the OCR package installed at all?

    Unlike ocr_available() this does not load the ONNX models, so page loads
    stay fast.
    """
    try:
        return importlib.util.find_spec("rapidocr") is not None
    except (ImportError, ValueError):
        return False


def extract_text(image_path):
    """Return the text found in an image, one detected line per row.

    image_path is the absolute path to the stored image file. An empty string
    means no text was found (or OCR is unavailable), never an exception.
    """
    if not image_path or not os.path.exists(image_path):
        return ""

    # Reject corrupt uploads before paying for the model load.
    if not _readable_image(image_path):
        logger.warning("OCR skipped an unreadable image: %s", image_path)
        return ""

    engine = _get_engine()
    if engine is None:
        return ""

    try:
        result = engine(image_path)
    except Exception as exc:
        logger.warning("OCR failed for %s: %s", image_path, exc)
        return ""

    texts = getattr(result, "txts", None) or ()
    lines = [str(line).strip() for line in texts if str(line).strip()]
    return "\n".join(lines)
