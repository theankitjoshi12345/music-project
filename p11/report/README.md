# Report source and regeneration

`report-data.json` contains the factual text mapped to the supplied official
template. It reflects the live Firebase/Cloud Run launch, the successful
protected-main pipeline, and the completed real non-team walkthrough.
`build_report.py` validates the retained template hash, fills its paragraph and
table slots, and preserves all OOXML package parts except the edited document
body. The original template remains unchanged.

Run the builder with Python 3 and `lxml`:

```bash
python3 p11/report/build_report.py
```

The builder embeds two dated public-launch screenshots. Then render
`P11-Report.docx` to PDF and inspect every page before replacing
`P11-Report.pdf`. A source edit is not complete until both outputs agree.

For Codex document work, use the bundled workspace Python/LibreOffice and the
documents skill's `render_docx.py --emit_pdf`. Page PNGs belong in a temporary QA
directory rather than the submission. Never use an old PDF after editing the
Word source.

The tester record is source evidence: it identifies the outside tester, date,
task, observed initial delay, follow-up, and successful retest.
