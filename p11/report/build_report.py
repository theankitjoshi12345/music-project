#!/usr/bin/env python3
"""Fill the retained P11 template without rewriting unrelated OOXML parts.

Run with Python and lxml, then render the DOCX and inspect every page before
submission. report-data.json is the editable factual source. The official
template is immutable; a hash check prevents accidental edits going unnoticed.
"""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "P11-Report-template.docx"
TEMPLATE_SHA256 = "bade80141871a5764ca6264e921ed81023bc8eef948d5062e5a005e77b8dda6a"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{" + NS["w"] + "}"


def element(name, **attributes):
    node = etree.Element(W + name)
    for name, value in attributes.items():
        node.set(W + name, str(value))
    return node


def properties(node, name):
    found = node.find(W + name)
    if found is None:
        found = element(name)
        node.insert(0, found)
    return found


def set_text(paragraph, text):
    """Keep the source paragraph role and replace only its editable content."""
    for child in list(paragraph):
        if child.tag != W + "pPr":
            paragraph.remove(child)
    run = element("r")
    value = element("t")
    value.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    value.text = text
    run.append(value)
    paragraph.append(run)


def main():
    if hashlib.sha256(TEMPLATE.read_bytes()).hexdigest() != TEMPLATE_SHA256:
        raise RuntimeError("Official template changed; inspect and redistill it first.")
    data = json.loads((HERE / "report-data.json").read_text())
    with ZipFile(TEMPLATE) as original:
        root = etree.fromstring(original.read("word/document.xml"))
        paragraphs = root.findall(".//w:p", NS)
        for index, value in data["paragraphs"].items():
            set_text(paragraphs[int(index)], value)

        # The source title uses Heading1; apply the document's real Title role.
        title_props = properties(paragraphs[0], "pPr")
        title_props.find(W + "pStyle").set(W + "val", "Title")
        title_props.append(element("jc", val="left"))

        # Keep the template's hierarchy, type sizes, tables, and section order.
        # Black headings improve print legibility without a new design system.
        for paragraph in paragraphs:
            props = paragraph.find(W + "pPr")
            role = props.find(W + "pStyle") if props is not None else None
            role_name = role.get(W + "val") if role is not None else ""
            if role_name in {"Title", "Heading1", "Heading2", "Heading3"}:
                for run in paragraph.findall(".//w:r", NS):
                    rprops = properties(run, "rPr")
                    rprops.append(element("color", val="000000"))
            # Keep short factual paragraphs together across page boundaries.
            if paragraph.getparent() is not None:
                properties(paragraph, "pPr").append(element("keepLines"))
            # Template separator rules are optional furniture, not content.
            if paragraph.find(".//w:pict", NS) is not None:
                parent = paragraph.getparent()
                parent.remove(paragraph)

        for table_index, table in enumerate(root.findall(".//w:tbl", NS)):
            props = properties(table, "tblPr")
            border = properties(props, "tblBorders")
            for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
                border.append(element(edge, val="single", sz="4", color="D9D9D9"))
            # Preserve the source's 5.5-inch table width while giving prose room.
            widths = [1600, 1000, 5320] if table_index == 0 else [3000, 4920]
            grid = table.find(W + "tblGrid")
            for column, width in zip(grid, widths):
                column.set(W + "w", str(width))
            for row_index, row in enumerate(table.findall("w:tr", NS)):
                row_props = properties(row, "trPr")
                row_props.append(element("cantSplit"))
                if row_index == 0:
                    row_props.append(element("tblHeader"))
                for column_index, cell in enumerate(row.findall("w:tc", NS)):
                    cell_props = properties(cell, "tcPr")
                    cell_width = properties(cell_props, "tcW")
                    cell_width.set(W + "w", str(widths[column_index]))
                    cell_width.set(W + "type", "dxa")
                    cell_props.append(element("vAlign", val="center"))
                    borders = properties(cell_props, "tcBorders")
                    for edge in ["top", "left", "bottom", "right"]:
                        borders.append(element(edge, val="single", sz="4", color="D9D9D9"))
                    margin = properties(cell_props, "tcMar")
                    for side in ["top", "bottom", "left", "right"]:
                        margin.append(element(side, w="90", type="dxa"))
                    if row_index == 0:
                        cell_props.append(element("shd", fill="EDEDED"))

        result = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        output = HERE / "P11-Report.docx"
        with ZipFile(output, "w", ZIP_DEFLATED) as final:
            for member in original.infolist():
                final.writestr(member, result if member.filename == "word/document.xml"
                               else original.read(member.filename))

    with ZipFile(TEMPLATE) as original, ZipFile(output) as final:
        unchanged = [name for name in original.namelist() if name != "word/document.xml"]
        assert all(original.read(name) == final.read(name) for name in unchanged)
    assert hashlib.sha256(TEMPLATE.read_bytes()).hexdigest() == TEMPLATE_SHA256
    print(f"Created {output}; {len(unchanged)} untouched package parts verified.")


if __name__ == "__main__":
    main()
