"""Small, dependency-free score metadata extraction helpers.

MusicXML is structured score data, so measure metadata can be imported without
guessing. A PDF is visual notation and needs an OMR engine to identify measures;
the upload workflow keeps those parts available for manual measure setup instead.
"""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree


class OMRUnavailable(RuntimeError):
    """Raised when the optional local Audiveris runtime is not configured."""


@dataclass
class PDFExtraction:
    measures: list
    page_count: int


def _xml_bytes(uploaded_file, suffix):
    uploaded_file.seek(0)
    if suffix != ".mxl":
        return uploaded_file.read()
    with ZipFile(uploaded_file) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith((".musicxml", ".xml")) and not name.startswith("META-INF/")]
        if "META-INF/container.xml" in archive.namelist():
            container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
            rootfile = next((element.get("full-path") for element in container.iter()
                             if element.tag.rsplit("}", 1)[-1] == "rootfile"), None)
            if rootfile in names:
                names.remove(rootfile)
                names.insert(0, rootfile)
        if not names:
            raise ValueError("The MXL file does not contain a MusicXML score.")
        if archive.getinfo(names[0]).file_size > 20 * 1024 * 1024:
            raise ValueError("The uncompressed MusicXML score exceeds 20 MB.")
        return archive.read(names[0])


def extract_musicxml_measures(uploaded_file):
    """Return (section, measure_number, page_number) for the first score part."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".musicxml", ".xml", ".mxl"}:
        return []
    try:
        root = ElementTree.parse(BytesIO(_xml_bytes(uploaded_file, suffix))).getroot()
    except (ElementTree.ParseError, OSError, ValueError, BadZipFile) as error:
        raise ValueError("The uploaded MusicXML file could not be read.") from error
    finally:
        uploaded_file.seek(0)

    part = next((element for element in root if element.tag.rsplit("}", 1)[-1] == "part"), None)
    if part is None:
        raise ValueError("The MusicXML file does not contain a score part.")

    measures = []
    page_number = 1
    section = "Start"
    for position, measure in enumerate((element for element in part if element.tag.rsplit("}", 1)[-1] == "measure"), start=1):
        for child in measure.iter():
            name = child.tag.rsplit("}", 1)[-1]
            if name == "print" and child.get("new-page") == "yes" and measures:
                page_number += 1
            if name == "rehearsal" and (child.text or "").strip():
                section = (child.text or "").strip()[:80]
        match = re.search(r"\d+", measure.get("number", ""))
        number = int(match.group()) if match else position
        measures.append((section, number, page_number))
    if not measures:
        raise ValueError("The MusicXML file does not contain any measures.")
    return measures


def extract_pdf_measures(pdf_path, audiveris_command, *, timeout=300, max_pages=10):
    """Run a local PDF → image → Audiveris → MXL pipeline.

    Results are globally numbered because each OMR page is exported separately
    and would otherwise restart its measure numbering at one.
    """
    executable = shutil.which(audiveris_command) if audiveris_command else None
    if not executable:
        raise OMRUnavailable("PDF measure extraction is unavailable until AUDIVERIS_COMMAND is configured.")
    if not shutil.which("pdftoppm") or not shutil.which("pdfinfo"):
        raise OMRUnavailable("PDF measure extraction requires Poppler (pdftoppm and pdfinfo).")

    info = subprocess.run(["pdfinfo", str(pdf_path)], check=True, capture_output=True, text=True, timeout=15)
    match = re.search(r"^Pages:\s+(\d+)", info.stdout, re.MULTILINE)
    if not match:
        raise ValueError("The PDF page count could not be read. Try an unencrypted PDF.")
    page_count = int(match.group(1))
    if page_count > max_pages:
        raise ValueError(f"This demo supports extraction of PDFs up to {max_pages} pages.")

    with tempfile.TemporaryDirectory(prefix="score-companion-omr-") as work:
        work_path = Path(work)
        image_prefix = work_path / "page"
        subprocess.run(["pdftoppm", "-png", "-r", "300", str(pdf_path), str(image_prefix)], check=True, capture_output=True, text=True, timeout=60)
        images = sorted(work_path.glob("page-*.png"), key=lambda path: int(path.stem.split("-")[-1]))
        if not images:
            raise ValueError("The PDF did not contain any renderable pages.")
        output = work_path / "output"
        output.mkdir()
        subprocess.run([executable, "-batch", "-transcribe", "-export", "-output", str(output), "--", *map(str, images)], check=True, capture_output=True, text=True, timeout=timeout)
        extracted = []
        number = 0
        for image in images:
            page_number = int(image.stem.split("-")[-1])
            exports = list(output.rglob(f"{image.stem}.mxl"))
            if not exports:
                raise ValueError(f"No measures were recognized on PDF page {page_number}. Existing saved measures were kept.")
            path = exports[0]
            with path.open("rb") as musicxml:
                page_measures = extract_musicxml_measures(musicxml)
            for _ in page_measures:
                number += 1
                extracted.append((f"Page {page_number}", number, page_number))
        if not extracted:
            raise ValueError("Audiveris did not identify any measures in this PDF.")
        return PDFExtraction(extracted, page_count)
