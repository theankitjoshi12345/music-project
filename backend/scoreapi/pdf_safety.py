"""Bound raster work before Poppler allocates page images."""

import math
import re
import subprocess


MAX_PAGE_POINTS = 1440  # 20 inches; ordinary Letter/A4 scores are much smaller.
MAX_PAGE_PIXELS = 25_000_000  # At the pipeline's highest resolution, 300 DPI.


class PDFSafetyError(ValueError):
    pass


def _check_dimensions(page, width, height):
    if not all(math.isfinite(value) and value > 0 for value in (width, height)):
        raise PDFSafetyError(f"PDF page {page} has invalid dimensions. Export it again and retry.")
    pixels = math.ceil(width * 300 / 72) * math.ceil(height * 300 / 72)
    if max(width, height) > MAX_PAGE_POINTS or pixels > MAX_PAGE_PIXELS:
        raise PDFSafetyError(f"PDF page {page} is too large to process safely. Export standard Letter or A4 pages and retry.")


def validate_pdf_pages(pdf_path, *, first_page=1, last_page=10, max_pages=None):
    """Inspect each requested page, including its full uncropped MediaBox.

    Extraction requests the complete allowed range before rendering any page.
    Preview rendering checks its selected page even when OMR has never run.
    """
    result = subprocess.run(
        ["pdfinfo", "-f", str(first_page), "-l", str(last_page), "-box", str(pdf_path)],
        check=True, capture_output=True, text=True, timeout=15,
    )
    counts = re.findall(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    if len(counts) != 1:
        raise PDFSafetyError("The PDF page count could not be read. Try an unencrypted PDF.")
    page_count = int(counts[0])
    if max_pages is not None and page_count > max_pages:
        raise PDFSafetyError(f"This demo supports extraction of PDFs up to {max_pages} pages.")
    expected = set(range(first_page, min(last_page, page_count) + 1))
    if not expected:
        raise PDFSafetyError("That PDF page does not exist.")
    sizes, media = {}, {}
    try:
        for page, width, height in re.findall(r"^Page\s+(\d+)\s+size:\s+(\S+)\s+x\s+(\S+)\s+pts", result.stdout, re.MULTILINE):
            number = int(page)
            if number in sizes:
                raise ValueError("Duplicate page information")
            sizes[number] = (float(width), float(height))
        for page, x1, y1, x2, y2 in re.findall(r"^Page\s+(\d+)\s+MediaBox:\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$", result.stdout, re.MULTILINE):
            number = int(page)
            if number in media:
                raise ValueError("Duplicate page information")
            media[number] = (float(x2) - float(x1), float(y2) - float(y1))
    except ValueError as error:
        raise PDFSafetyError("The PDF page dimensions could not be verified. Export the PDF again and retry.") from error
    if set(sizes) != expected or set(media) != expected:
        raise PDFSafetyError("The PDF page dimensions could not be verified. Export the PDF again and retry.")
    for page in expected:
        _check_dimensions(page, *sizes[page])
        _check_dimensions(page, *media[page])
    return page_count
