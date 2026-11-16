# Report source and regeneration

`report-data.json` contains the factual text mapped to the supplied official
template. It reflects the live Firebase/Cloud Run launch and the successful
protected-main pipeline. Update the outside-user line only after a real
non-team walkthrough is recorded.
`build_report.py` validates the retained template hash, fills its paragraph and
table slots, and preserves all OOXML package parts except the edited document
body. The original template remains unchanged.

Run the builder with Python 3 and `lxml`:

```bash
python3 p11/report/build_report.py
```

The builder also embeds the dated public-launch screenshot. Then render
`P11-Report.docx` to PDF and inspect every page before replacing
`P11-Report.pdf`. A source edit is not complete until both outputs agree.

For Codex document work, use the bundled workspace Python/LibreOffice and the
documents skill's `render_docx.py --emit_pdf`. Page PNGs belong in a temporary QA
directory rather than the submission. Never use an old PDF after editing the
Word source.

The only pending report item is the actual outside-user walkthrough. Updating a
status in this file does not establish that the corresponding test occurred.
