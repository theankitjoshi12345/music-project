"""Small, dependency-free score metadata extraction helpers.

MusicXML is structured score data, so measure metadata can be imported without
guessing. A PDF is visual notation and needs an OMR engine to identify measures;
the upload workflow keeps those parts available for manual measure setup instead.
"""

from io import BytesIO
from pathlib import Path
import re
from zipfile import ZipFile
from xml.etree import ElementTree


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
