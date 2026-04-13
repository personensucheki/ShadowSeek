from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from werkzeug.utils import secure_filename


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_IMAGE_TYPES = {"png", "jpeg", "webp", "gif"}


def validate_image_upload(file_obj, *, max_size_bytes: int) -> tuple[str, bytes]:
    if not file_obj or not file_obj.filename:
        raise ValueError("No image file provided.")

    filename = secure_filename(file_obj.filename)
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Unsupported image extension.")

    raw = file_obj.read()
    file_obj.stream.seek(0)
    if not raw:
        raise ValueError("Uploaded image is empty.")
    if len(raw) > max_size_bytes:
        raise ValueError("Uploaded image exceeds size limit.")

    try:
        with Image.open(io.BytesIO(raw)) as image:
            image_format = (image.format or "").lower()
            image.load()
    except Exception as error:
        raise ValueError("Corrupted or unsupported image data.") from error
    if image_format not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Uploaded file is not a valid image.")

    return filename, raw
