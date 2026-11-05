# Report source and regeneration

`report-data.json` contains the factual text mapped to the supplied official
template. Edit those values when real verification evidence becomes available.
`build_report.py` validates the retained template hash, fills its paragraph and
table slots, and preserves all OOXML package parts except the edited document
body. The original template remains unchanged.

Run the builder with Python 3 and `lxml`:

```bash
python3 p11/report/build_report.py
```

Then export `P11-Report.docx` to PDF and inspect every page before replacing
`P11-Report.pdf`. A source edit is not complete until both outputs agree.

For Codex document work, use the bundled workspace Python/LibreOffice and the
documents skill's `render_docx.py --emit_pdf`. Page PNGs belong in a temporary QA
directory rather than the submission. Never use an old PDF after editing the
Word source.

The current report is incomplete while public deployment, successful pipeline,
actual launch screenshots, and outside-user testing are pending. Updating a
status in this file does not establish that the corresponding test occurred.
