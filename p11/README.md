# P11 Launch submission

**Score Companion · Team 08 · CMPS453 · Due November 9, 2026**

P11 makes the completed P10 workflow available publicly, with repeatable
delivery and documented application and infrastructure security.

**Free demo URL:** https://locate-valuation-using-donald.trycloudflare.com

This is a temporary Cloudflare Quick Tunnel backed by Docker on the development
computer. It is HTTPS and was verified with the real PDF-to-measure workflow,
but it stops when the tunnel container stops and its address is not permanent.
No billing, paid hosting, or billable cloud resource is used.

## Project documentation

- [Root project guide and user instructions](../README.md)
- [Root architecture](../architecture.md)
- [Completed P10 report](../p10/P10_Integrated_MVP_Report.docx)

## Assignment files

- [Organized instructions](instruction.md)
- [Rubric and launch checklist](launch-checklist.md)
- [Official report template](P11-Report-template.docx)
- [Official grader notes](P11-grader-notes.docx)
- [Word report](report/P11-Report.docx)
- [PDF report](report/P11-Report.pdf)
- [Editable report data](report/report-data.json) and [report builder](report/build_report.py)
- [Evidence index](evidence/README.md)
- [Team contribution record](team-contributions.md)
- [Actual outside-user test record](outside-user-test.md)

## Evidence status

| Area | Evidence |
| --- | --- |
| Public launch, core task, persistence | Temporary free HTTPS demo verified; durable production hosting and outside-user evidence remain pending. |
| GitLab CI/CD | Configuration linted; execution blocked until the GitLab account completes identity verification. |
| Security | Production checks, restart persistence, and live two-session isolation verified; permanent-host controls remain out of scope. |
| Report | Regenerated from the official template and visually verified; remaining human-only fields stay explicit. |
| Outside-user testing | Pending an actual person outside Team 08. |

## Remaining human actions

An actual non-team person must try the deployed product and provide the record
described in `outside-user-test.md`. Completed assigned issue evidence for all
four members is recorded in `team-contributions.md`. A durable public host would
require a separately approved free-tier or paid service; that work is
intentionally out of scope for this free demo.

No video is included. The official template places the final presentation and
live demo in P13.
