"""Small, dependency-free score metadata extraction helpers.

MusicXML is structured score data, so measure metadata can be imported without
guessing. A PDF is visual notation and needs an OMR engine to identify measures;
the upload workflow keeps those parts available for manual measure setup instead.
"""

from io import BytesIO
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import ZipFile
from xml.etree import ElementTree


class OMRUnavailable(RuntimeError):
    """Raised when the optional local Audiveris runtime is not configured."""


def _xml_bytes(uploaded_file, suffix):
    uploaded_file.seek(0)
    if suffix != ".mxl":
        return uploaded_file.read()
    with ZipFile(uploaded_file) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith((".musicxml", ".xml")) and not name.startswith("META-INF/")]
        if not names:
            raise ValueError("The MXL file does not contain a MusicXML score.")
        return archive.read(names[0])


def extract_musicxml_measures(uploaded_file):
    """Return (section, measure_number, page_number) for the first score part."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".musicxml", ".xml", ".mxl"}:
        return []
    try:
        root = ElementTree.parse(BytesIO(_xml_bytes(uploaded_file, suffix))).getroot()
    except (ElementTree.ParseError, OSError, ValueError) as error:
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


def extract_pdf_measures(pdf_path, audiveris_command):
    """Run a local PDF → image → Audiveris → MXL pipeline.

    Results are globally numbered because each OMR page is exported separately
    and would otherwise restart its measure numbering at one.
    """
    if not audiveris_command or not Path(audiveris_command).is_file():
        raise OMRUnavailable("PDF measure extraction is unavailable until AUDIVERIS_COMMAND is configured.")
    if not shutil.which("pdftoppm"):
        raise OMRUnavailable("PDF measure extraction requires the pdftoppm utility.")

    with tempfile.TemporaryDirectory(prefix="score-companion-omr-") as work:
        work_path = Path(work)
        image_prefix = work_path / "page"
        subprocess.run(["pdftoppm", "-png", "-r", "300", str(pdf_path), str(image_prefix)], check=True, capture_output=True, text=True)
        images = sorted(work_path.glob("page-*.png"))
        if not images:
            raise ValueError("The PDF did not contain any renderable pages.")
        output = work_path / "output"
        output.mkdir()
        subprocess.run([audiveris_command, "-batch", "-transcribe", "-export", "-output", str(output), "--", *map(str, images)], check=True, capture_output=True, text=True, timeout=300)
        extracted = []
        number = 0
        for page_number, path in enumerate(sorted(output.glob("*.mxl")), start=1):
            with path.open("rb") as musicxml:
                page_measures = extract_musicxml_measures(musicxml)
            for _, _, _ in page_measures:
                number += 1
                extracted.append((f"Page {page_number}", number, page_number))
        if not extracted:
            raise ValueError("Audiveris did not identify any measures in this PDF.")
        return extracted
