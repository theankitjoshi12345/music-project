from pathlib import Path
import subprocess
import struct
from unittest.mock import patch
from zipfile import ZipFile

from django.test import SimpleTestCase

from .score_extract import extract_pdf_measures


class PDFExtractionTests(SimpleTestCase):
    @patch("scoreapi.score_extract.shutil.which", side_effect=lambda command: command)
    @patch("scoreapi.score_extract.subprocess.run")
    def test_page_number_mapping_survives_nested_exports_and_double_digit_pages(self, run, which):
        def command(args, **kwargs):
            if args[0] == "pdfinfo":
                return subprocess.CompletedProcess(args, 0, stdout="Pages: 10\n")
            if args[0] == "pdftoppm":
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
        result = extract_pdf_measures("test.pdf", "audiveris")
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
                return subprocess.CompletedProcess(args, 0, stdout="Pages: 2\n")
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
