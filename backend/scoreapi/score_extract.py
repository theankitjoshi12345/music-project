"""Small, dependency-free score metadata extraction helpers.

MusicXML is structured score data, so measure metadata can be imported without
guessing. A PDF is visual notation and needs an OMR engine to identify measures;
the upload workflow keeps those parts available for manual measure setup instead.
"""

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import struct
from zipfile import BadZipFile, ZipFile
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from .pdf_safety import validate_pdf_pages


MAX_XML_BYTES = 20 * 1024 * 1024
MAX_MXL_MANIFEST_BYTES = 64 * 1024
MAX_MXL_ENTRIES = 1000
MAX_MUSICXML_MEASURES = 10000


class OMRUnavailable(RuntimeError):
    """Raised when the optional local Audiveris runtime is not configured."""


@dataclass
class PDFExtraction:
    measures: list
    page_count: int
    regions: dict = field(default_factory=dict)


def extract_measure_regions(omr_path):
    """Read original-image coordinates from Audiveris measure stacks.

    Stack IDs match the exported MusicXML measure numbers. A stack spans all
    staves in a system, so piano previews include both hands. Coordinates are
    normalized to the PNG size used for recognition.
    """
    with ZipFile(omr_path) as archive:
        sheet_path = next((name for name in archive.namelist()
                           if re.fullmatch(r"sheet#\d+/sheet#\d+\.xml", name)), None)
        if not sheet_path:
            raise ValueError("Recognition did not provide a page layout.")
        root = ElementTree.fromstring(archive.read(sheet_path))
        png_name = sheet_path.rsplit("/", 1)[0] + "/BINARY.png"
        image = archive.read(png_name)
        if image[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Recognition returned an invalid page image.")
        width, height = struct.unpack(">II", image[16:24])
    regions = {}
    for system in root.findall("./page/system"):
        staves = system.findall("./part/staff")
        points = [point for staff in staves for point in staff.findall("./lines/line/point")]
        if not points:
            continue
        ys = [float(point.get("y")) for point in points]
        lines = staves[0].findall("./lines/line")
        line_ys = [sum(float(point.get("y")) for point in line.findall("point")) / len(line.findall("point"))
                   for line in lines if line.findall("point")]
        interline = (max(line_ys) - min(line_ys)) / max(1, len(line_ys) - 1)
        # Include ledger lines, dynamics and articulation marks around the staff.
        top = max(0, min(ys) - 8 * interline)
        bottom = min(height, max(ys) + 5 * interline)
        for stack in system.findall("stack"):
            if stack.get("special") == "CAUTIONARY":
                continue
            left = max(0, float(stack.get("left")) - interline / 2)
            right = min(width, float(stack.get("right")) + interline / 2)
            if right > left and bottom > top:
                regions[stack.get("id")] = {"x": left / width, "y": top / height,
                    "width": (right - left) / width, "height": (bottom - top) / height,
                    "image_width": width, "image_height": height}
    return regions


def _xml_bytes(uploaded_file, suffix):
    uploaded_file.seek(0)
    if suffix != ".mxl":
        data = uploaded_file.read(MAX_XML_BYTES + 1)
        if len(data) > MAX_XML_BYTES:
            raise ValueError("The MusicXML score exceeds 20 MB.")
        return data
    with ZipFile(uploaded_file) as archive:
        if len(archive.infolist()) > MAX_MXL_ENTRIES:
            raise ValueError("The MXL archive contains too many entries.")
        names = [name for name in archive.namelist() if name.lower().endswith((".musicxml", ".xml")) and not name.startswith("META-INF/")]
        if "META-INF/container.xml" in archive.namelist():
            if archive.getinfo("META-INF/container.xml").file_size > MAX_MXL_MANIFEST_BYTES:
                raise ValueError("The MXL manifest exceeds 64 KB.")
            container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
            rootfile = next((element.get("full-path") for element in container.iter()
                             if element.tag.rsplit("}", 1)[-1] == "rootfile"), None)
            if rootfile in names:
                names.remove(rootfile)
                names.insert(0, rootfile)
        if not names:
            raise ValueError("The MXL file does not contain a MusicXML score.")
        if archive.getinfo(names[0]).file_size > MAX_XML_BYTES:
            raise ValueError("The uncompressed MusicXML score exceeds 20 MB.")
        return archive.read(names[0])


def extract_musicxml_measures(uploaded_file):
    """Return (section, measure_number, page_number) for the first score part."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".musicxml", ".xml", ".mxl"}:
        return []
    try:
        root = ElementTree.parse(BytesIO(_xml_bytes(uploaded_file, suffix))).getroot()
    except (ElementTree.ParseError, DefusedXmlException, OSError, ValueError, BadZipFile, RuntimeError, NotImplementedError) as error:
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
        if position > MAX_MUSICXML_MEASURES:
            raise ValueError(f"This demo supports MusicXML scores up to {MAX_MUSICXML_MEASURES} measures.")
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


def extract_pdf_measures(pdf_path, audiveris_command, *, timeout=300, max_pages=10, on_page_count=None):
    """Run a local PDF → image → Audiveris → MXL pipeline.

    Results are globally numbered because each OMR page is exported separately
    and would otherwise restart its measure numbering at one.
    """
    executable = shutil.which(audiveris_command) if audiveris_command else None
    if not executable:
        raise OMRUnavailable("PDF measure extraction is unavailable until AUDIVERIS_COMMAND is configured.")
    if not shutil.which("pdftoppm") or not shutil.which("pdfinfo"):
        raise OMRUnavailable("PDF measure extraction requires Poppler (pdftoppm and pdfinfo).")

    page_count = validate_pdf_pages(pdf_path, last_page=max_pages, max_pages=max_pages)
    if on_page_count:
        on_page_count(page_count)

    with tempfile.TemporaryDirectory(prefix="score-companion-omr-") as work:
        work_path = Path(work)
        image_prefix = work_path / "page"
        subprocess.run(["pdftoppm", "-png", "-r", "300", str(pdf_path), str(image_prefix)], check=True, capture_output=True, text=True, timeout=60)
        images = sorted(work_path.glob("page-*.png"), key=lambda path: int(path.stem.split("-")[-1]))
        if not images:
            raise ValueError("The PDF did not contain any renderable pages.")
        output = work_path / "output"
        output.mkdir()
        subprocess.run([executable, "-batch", "-save", "-transcribe", "-export", "-output", str(output), "--", *map(str, images)], check=True, capture_output=True, text=True, timeout=timeout)
        extracted = []
        regions = {}
        number = 0
        for image in images:
            page_number = int(image.stem.split("-")[-1])
            exports = list(output.rglob(f"{image.stem}.mxl"))
            if not exports:
                raise ValueError(f"No measures were recognized on PDF page {page_number}. Existing saved measures were kept.")
            path = exports[0]
            with path.open("rb") as musicxml:
                page_measures = extract_musicxml_measures(musicxml)
                musicxml.seek(0)
                xml_root = ElementTree.fromstring(_xml_bytes(musicxml, ".mxl"))
            part = next(element for element in xml_root if element.tag.rsplit("}", 1)[-1] == "part")
            measure_ids = [element.get("number", "") for element in part if element.tag.rsplit("}", 1)[-1] == "measure"]
            layouts = list(output.rglob(f"{image.stem}.omr"))
            if not layouts:
                raise ValueError(f"No measure positions were saved for PDF page {page_number}.")
            page_regions = extract_measure_regions(layouts[0])
            for measure_id, _ in zip(measure_ids, page_measures, strict=True):
                if measure_id not in page_regions:
                    raise ValueError(f"The position of measure {measure_id} on page {page_number} could not be found.")
                number += 1
                key = (f"Page {page_number}", number, page_number)
                extracted.append(key)
                regions[key] = page_regions[measure_id]
        if not extracted:
            raise ValueError("Audiveris did not identify any measures in this PDF.")
        return PDFExtraction(extracted, page_count, regions)
