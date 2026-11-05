# P11 launch evidence checklist

Updated November 5, 2026. An unchecked item is not verified for the public launch.
The user mission makes actual outside-user testing mandatory even though the
grader notes say to note an outside tester when possible.

| Requirement | Rubric mapping | Status and required evidence |
| --- | --- | --- |
| Public HTTPS URL works independently of a developer machine | Launch 30% | Temporary HTTPS URL verified from fresh sessions; it still depends on the developer computer and is not permanent hosting. |
| New user completes upload → recognition → measure → practice review | Launch 30% | Public PDF recognition and measure preview verified; full outside-user practice-review walkthrough remains pending. |
| Uploaded PDFs, measures, and notes survive restart/redeploy | Launch 30%; security 20% | Docker container recreation preserved scores, PDFs, and 112 passages; host-loss recovery remains unverified. |
| Existing P10 workflow remains usable | Launch 30% | Backend 54 tests, frontend 24 tests, production build, public recognition, and measure preview passed. |
| Real non-team person completes or attempts core task | Launch 30% | Pending actual person; record in [outside-user-test.md](outside-user-test.md). |
| README explains public access and core task | Documentation 25% | Verified temporary URL, Docker command, limitations, and user flow are documented. |
| Local, Docker, and cloud setup are clearly separated | Documentation 25% | Root README and free-demo guide distinguish local, free tunnel, and inactive paid proposal. |
| Local, Docker, production, and CI diagrams reflect reality | Documentation 25% | Architecture updated for private sessions, Docker recognition, free tunnel, and gated paid proposal. |
| GitLab CI runs backend/frontend checks and dependency scans | CI/CD 20% | Configuration linted and routed to online free ULL group runners; GitLab still blocks pipeline creation until account identity verification. |
| Deployment is repeatable after required checks | CI/CD 20% | One Docker command is repeatable locally; GitLab deployment execution remains blocked and paid deployment is disabled. |
| CI secrets are protected and absent from Git/frontend | CI/CD 20%; security 20% | Ignore/Docker-exclude rules and short-lived CI identity design reviewed; no secret value is recorded as evidence. |
| Users cannot read or change another visitor's data/files | Security 20% | Live two-session read/delete isolation passed; 54 backend tests cover all protected route families. |
| Production DEBUG, hosts, CSRF, cookies, HTTPS, and admin are safe | Security 20% | Production Django check passed; HTTPS session mode and blocked direct media/admin routes were exercised. |
| Persistent database/files are private; cleanup removes owned data | Security 20% | Restart persistence and owner-only cleanup verified with a disposable public record. |
| Recognition resource/time limits and failure handling are documented | Security 20%; launch 30% | Quotas, one-job lock, PDF/XML bounds, failure states, and countdown behavior are implemented and documented. |
| Native and Docker startup/tests still pass | Launch 30%; documentation 25% | 54 backend tests, 24 frontend tests, build, Docker health, and public health passed. |
| Report uses official template and exports cleanly to PDF | Polish 5% | Word and PDF regenerated from the official template and visually inspected across four pages. |
| Screenshots show real launched environment | Polish 5%; launch 30% | Pending; no localhost screenshots substituted. |
| Team schedule reflects actual work | Polish 5% | Completed assigned issues #31 through #34 and P11 MRs #30 through #32 are linked in [contributions](team-contributions.md). |
| Challenges, resolutions, and remaining limitations are specific | Polish 5%; security 20% | In progress in report. |
| Root docs, report, links, and repository state agree | Polish 5% | Local, GitLab, and GitHub synchronization checks passed; final history records the documentation merge. |

## Submission checks

- [x] Official template and grader notes retained unchanged.
- [x] P11 instructions organized separately from project source.
- [x] Previous assignment material remains in place.
- [x] Temporary free public demo verified; permanent hosting is not claimed.
- [ ] Successful GitLab pipeline captured after identity verification.
- [x] CI/CD blocker and static validation evidence captured; successful run remains pending.
- [x] Security evidence captured.
- [ ] Real launch screenshots added.
- [ ] Actual outside-user test recorded.
- [x] Team contribution issue URLs recorded as directed.
- [x] Final Word and PDF report regenerated and visually inspected.
- [x] Final links, commits, and GitLab/GitHub synchronization checked.
