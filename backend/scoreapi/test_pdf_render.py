import subprocess
from unittest.mock import patch

from django.test import SimpleTestCase

from .pdf_render import render_pdf


class PDFRenderTests(SimpleTestCase):
    @patch("scoreapi.pdf_render.validate_pdf_pages")
    @patch("scoreapi.pdf_render.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout=b"\x89PNG\r\n\x1a\nimage"))
    def test_preview_renders_the_selected_page_and_original_pixel_region(self, run, inspect):
        region = {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4, "image_width": 1000, "image_height": 1400}
        render_pdf("score.pdf", 2, region)
        args = run.call_args.args[0]
        for flag, expected in [("-f", "2"), ("-l", "2"), ("-x", "100"), ("-y", "280"), ("-W", "300"), ("-H", "561")]:
            self.assertEqual(args[args.index(flag) + 1], expected)
        inspect.assert_called_once_with("score.pdf", first_page=2, last_page=2)

    @patch("scoreapi.pdf_render.subprocess.run")
    def test_invalid_region_cannot_render_an_unrelated_or_empty_page(self, run):
        with self.assertRaises(ValueError):
            render_pdf("score.pdf", 1, {"x": -1, "y": 0, "width": 1, "height": 1, "image_width": 1000, "image_height": 1000})
        run.assert_not_called()

    @patch("scoreapi.pdf_render.subprocess.run")
    def test_preview_rejects_large_pixel_area_without_running_poppler_rasterizer(self, run):
        # Both sides fit the physical bound, but 6000x6000 pixels exceeds 25 MP.
        run.return_value = subprocess.CompletedProcess([], 0, stdout="Pages: 1\nPage 1 size: 1440 x 1440 pts\nPage 1 MediaBox: 0 0 1440 1440\n")
        with self.assertRaisesRegex(ValueError, "too large to process safely"):
            render_pdf("giant.pdf", 1)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][0], "pdfinfo")
