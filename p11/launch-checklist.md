# P11 launch evidence checklist

Updated November 4, 2026. An unchecked item is not verified for the public launch.
The user mission makes actual outside-user testing mandatory even though the
grader notes say to note an outside tester when possible.

| Requirement | Rubric mapping | Status and required evidence |
| --- | --- | --- |
| Public HTTPS URL works independently of a developer machine | Launch 30% | Pending deployed URL and external/fresh-context check. |
| New user completes upload → recognition → measure → practice review | Launch 30% | Pending public end-to-end result; local P10 evidence is historical only. |
| Uploaded PDFs, measures, and notes survive restart/redeploy | Launch 30%; security 20% | Pending production persistence test. |
| Existing P10 workflow remains usable | Launch 30% | Pending launch regression checks. |
| Real non-team person completes or attempts core task | Launch 30% | Pending actual person; record in [outside-user-test.md](outside-user-test.md). |
| README explains public access and core task | Documentation 25% | Pending verified launch URL and production walkthrough. |
| Local, Docker, and cloud setup are clearly separated | Documentation 25% | Pending final root README review. |
| Local, Docker, production, and CI diagrams reflect reality | Documentation 25% | Pending final root architecture review. |
| GitLab CI runs backend/frontend checks and dependency scans | CI/CD 20% | Pending successful pipeline URL and saved result. |
| Deployment is repeatable after required checks | CI/CD 20% | Pending deployment and health-check jobs. |
| CI secrets are protected and absent from Git/frontend | CI/CD 20%; security 20% | Pending final configuration review; do not store secret values as evidence. |
| Users cannot read or change another visitor's data/files | Security 20% | Pending isolation tests for upload, detail, image, source file, extraction, and practice routes. |
| Production DEBUG, hosts, CSRF, cookies, HTTPS, and admin are safe | Security 20% | Pending deployment-check output and actual response inspection. |
| Persistent database/files are private; cleanup removes owned data | Security 20% | Pending production storage and cleanup evidence. |
| Recognition resource/time limits and failure handling are documented | Security 20%; launch 30% | Pending implementation review and deployed verification. |
| Native and Docker startup/tests still pass | Launch 30%; documentation 25% | Pending new launch-build results. |
| Report uses official template and exports cleanly to PDF | Polish 5% | In progress; [report source](report/report-data.json). |
| Screenshots show real launched environment | Polish 5%; launch 30% | Pending; no localhost screenshots substituted. |
| Team schedule reflects actual P11 work | Polish 5% | Pending supported member records; [contributions](team-contributions.md). |
| Challenges, resolutions, and remaining limitations are specific | Polish 5%; security 20% | In progress in report. |
| Root docs, report, links, and repository state agree | Polish 5% | Pending final consistency check after merge/deploy. |

## Submission checks

- [x] Official template and grader notes retained unchanged.
- [x] P11 instructions organized separately from project source.
- [x] Previous assignment material remains in place.
- [ ] Public launch verified.
- [ ] CI/CD evidence captured.
- [ ] Security evidence captured.
- [ ] Real launch screenshots added.
- [ ] Actual outside-user test recorded.
- [ ] Team contributions confirmed.
- [ ] Final Word and PDF report regenerated and visually inspected.
- [ ] Final links, commits, and GitLab/GitHub synchronization checked.
