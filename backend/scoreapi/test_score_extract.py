from pathlib import Path
from io import BytesIO
import subprocess
import struct
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from .score_extract import extract_musicxml_measures, extract_pdf_measures


def pdf_information(pages):
    return f"Pages: {pages}\n" + "".join(
        f"Page {number} size: 612 x 792 pts\nPage {number} MediaBox: 0 0 612 792\n"
        for number in range(1, pages + 1)
    )


class MusicXMLSafetyTests(SimpleTestCase):
    def test_oversized_compressed_manifest_is_rejected_before_decompression(self):
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("META-INF/container.xml", " " * (64 * 1024 + 1))
            archive.writestr("score.xml", '<score-partwise><part><measure number="1"/></part></score-partwise>')
        score = SimpleUploadedFile("bomb.mxl", output.getvalue())
        with patch("scoreapi.score_extract.ZipFile.read") as read:
            with self.assertRaisesRegex(ValueError, "could not be read"):
                extract_musicxml_measures(score)
            read.assert_not_called()

    def test_entity_definitions_are_rejected(self):
        data = b'<!DOCTYPE score-partwise [<!ENTITY private SYSTEM "file:///etc/passwd">]><score-partwise><part><measure number="1"><direction>&private;</direction></measure></part></score-partwise>'
        with self.assertRaisesRegex(ValueError, "could not be read"):
            extract_musicxml_measures(SimpleUploadedFile("entity.musicxml", data))

    def test_standard_musicxml_doctype_still_imports_without_fetching_external_dtd(self):
        data = b'<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd"><score-partwise><part><measure number="1"/></part></score-partwise>'
        self.assertEqual(extract_musicxml_measures(SimpleUploadedFile("standard.musicxml", data)), [("Start", 1, 1)])

    @patch("scoreapi.score_extract.MAX_MUSICXML_MEASURES", 2)
    def test_measure_limit_bounds_database_records_before_import(self):
        data = b'<score-partwise><part><measure number="1"/><measure number="2"/><measure number="3"/></part></score-partwise>'
        with self.assertRaisesRegex(ValueError, "up to 2 measures"):
            extract_musicxml_measures(SimpleUploadedFile("too-many.musicxml", data))


class PDFExtractionTests(SimpleTestCase):
    @patch("scoreapi.score_extract.shutil.which", side_effect=lambda command: command)
    @patch("scoreapi.score_extract.subprocess.run")
    def test_page_number_mapping_survives_nested_exports_and_double_digit_pages(self, run, which):
        page_counts = []
        def command(args, **kwargs):
            if args[0] == "pdfinfo":
                return subprocess.CompletedProcess(args, 0, stdout=pdf_information(10))
            if args[0] == "pdftoppm":
                self.assertEqual(page_counts, [10])
                for number in range(1, 11):
                    Path(f"{args[-1]}-{number}.png").touch()
            else:
                output = Path(args[args.index("-output") + 1])
                for image in args[args.index("--") + 1:]:
                    stem = Path(image).stem
                    folder = output / stem
                    folder.mkdir()
                    with ZipFile(folder / f"{stem}.mxl", "w") as archive:
                        archive.writestr("score.xml", '<score-partwise><part><measure number="1"/></part></score-partwise>')
                    with ZipFile(folder / f"{stem}.omr", "w") as archive:
                        archive.writestr("sheet#1/sheet#1.xml", '<sheet><page><system><stack id="1" left="100" right="500"/><part><staff><lines><line><point x="100" y="300"/><point x="500" y="300"/></line><line><point x="100" y="320"/><point x="500" y="320"/></line></lines></staff></part></system></page></sheet>')
                        archive.writestr("sheet#1/BINARY.png", b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR" + struct.pack(">II", 1000, 1400))
            return subprocess.CompletedProcess(args, 0, stdout="")

        run.side_effect = command
        result = extract_pdf_measures("test.pdf", "audiveris", on_page_count=page_counts.append)
        self.assertEqual(result.page_count, 10)
        self.assertEqual(result.measures[1], ("Page 2", 2, 2))
        self.assertEqual(result.measures[-1], ("Page 10", 10, 10))
        self.assertAlmostEqual(result.regions[("Page 2", 2, 2)]["x"], 0.09)
        self.assertGreater(result.regions[("Page 2", 2, 2)]["height"], 0)

    @patch("scoreapi.score_extract.shutil.which", side_effect=lambda command: command)
    @patch("scoreapi.score_extract.subprocess.run")
    def test_missing_page_export_fails_instead_of_silently_renumbering_pages(self, run, which):
        def command(args, **kwargs):
            if args[0] == "pdfinfo":
                return subprocess.CompletedProcess(args, 0, stdout=pdf_information(2))
            if args[0] == "pdftoppm":
                Path(f"{args[-1]}-1.png").touch()
                Path(f"{args[-1]}-2.png").touch()
            return subprocess.CompletedProcess(args, 0, stdout="")
        run.side_effect = command
        with self.assertRaisesRegex(ValueError, "page 1"):
            extract_pdf_measures("test.pdf", "audiveris")

    @patch("scoreapi.score_extract.shutil.which", side_effect=lambda command: command)
    @patch("scoreapi.score_extract.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout="Pages: 20\n"))
    def test_demo_page_limit_is_checked_before_rendering(self, run, which):
        with self.assertRaisesRegex(ValueError, "10 pages"):
            extract_pdf_measures("large.pdf", "audiveris")
        self.assertEqual(run.call_count, 1)

    @patch("scoreapi.score_extract.shutil.which", side_effect=lambda command: command)
    @patch("scoreapi.score_extract.subprocess.run")
    def test_oversized_second_page_is_rejected_before_any_page_is_rasterized(self, run, which):
        info = pdf_information(2).replace("Page 2 MediaBox: 0 0 612 792", "Page 2 MediaBox: 0 0 100000 100000")
        run.return_value = subprocess.CompletedProcess([], 0, stdout=info)
        with self.assertRaisesRegex(ValueError, "page 2 is too large"):
            extract_pdf_measures("giant.pdf", "audiveris")
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][0], "pdfinfo")
