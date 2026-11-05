"""Render the original PDF notation, including crops located by Audiveris."""

import math
import subprocess
from .pdf_safety import validate_pdf_pages


def render_pdf(pdf_path, page_number, region=None):
    args = ["pdftoppm", "-f", str(page_number), "-l", str(page_number), "-singlefile", "-png"]
    if region is not None:
        values = [region.get(key) for key in ["x", "y", "width", "height", "image_width", "image_height"]]
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
            raise ValueError("The saved measure position is invalid. Extract measures again.")
        x, y, width, height, image_width, image_height = values
        if not (0 <= x < 1 and 0 <= y < 1 and width > 0 and height > 0 and x + width <= 1.00001
                and y + height <= 1.00001 and 0 < image_width <= 20000 and 0 < image_height <= 20000):
            raise ValueError("The saved measure position is outside the score page.")
        left, top = math.floor(x * image_width), math.floor(y * image_height)
        right, bottom = math.ceil((x + width) * image_width), math.ceil((y + height) * image_height)
        args += ["-r", "300", "-x", str(left), "-y", str(top), "-W", str(right - left), "-H", str(bottom - top)]
    else:
        args += ["-r", "150"]
    validate_pdf_pages(pdf_path, first_page=page_number, last_page=page_number)
    result = subprocess.run([*args, str(pdf_path)], check=True, capture_output=True, timeout=30)
    if not result.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("The PDF page did not render an image.")
    return result.stdout
