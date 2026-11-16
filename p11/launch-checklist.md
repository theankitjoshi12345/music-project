# P11 launch checklist

Updated November 15, 2026. Evidence refers to the current public launch, not the retired Cloudflare tunnel.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Public HTTPS URL | Complete | [music-companion-513717.web.app](https://music-companion-513717.web.app) returns the public sign-in page and live session configuration. |
| Off the development laptop | Complete | Firebase Hosting and Cloud Run serve the public build. |
| P10a core task available | Complete | Google-authenticated private libraries, PDF/MusicXML upload, measure conversion, practice notes, review, and deletion are implemented and deployment-checked. |
| Launch documentation | Complete | Root README documents public access, user flow, local/Docker usage, production configuration names, and limits. |
| Repeatable CI/CD | Complete | [.gitlab-ci.yml](../.gitlab-ci.yml) runs build, tests, scans, package, deploy, and public verification; [pipeline 3071046544](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/pipelines/3071046544) succeeded. |
| Production security | Complete | Google sign-in, owner authorization, CSRF, secure cookies, private file routes, HTTPS, Secret Manager, Workload Identity Federation, bounded recognition, and deployment verification are documented in the root architecture. |
| Launched-build screenshot | Complete | [Public Google sign-in screenshot](evidence/launch/public-google-sign-in-2026-11-15.png). |
| Real outside-user walkthrough | Pending human action | Record the tester, date, device, result, and any fix in [outside-user-test.md](outside-user-test.md). |

## Submission gate

Attach `p11/report/P11-Report.pdf` and the Word report if requested after the outside-user row is completed. The report does not claim that pending test was performed.
