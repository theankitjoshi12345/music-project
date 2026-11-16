# P11 Launch submission

**Score Companion · Team 08 · CMPS453 · Due November 16, 2026, 11:55 PM**

Score Companion is live at [music-companion-513717.web.app](https://music-companion-513717.web.app). Firebase Hosting provides the public HTTPS frontend and Cloud Run provides the Django/PDF-recognition API.

## Submission files

- [Final Word report](report/P11-Report.docx)
- [Final PDF report](report/P11-Report.pdf)
- [Official report template](P11-Report-template.docx)
- [Official grader notes](P11-grader-notes.docx)
- [Web-app launch guide](P11-WebApp-Launch-Guide.pdf)
- [Live launch screenshot](evidence/launch/public-google-sign-in-2026-11-15.png)
- [Team contribution record](team-contributions.md)
- [Outside-user test record](outside-user-test.md)

## Launch and CI/CD evidence

The protected-main deployment for commit `dd3f569` completed successfully in [GitLab pipeline 3071046544](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/pipelines/3071046544). It ran backend, Firestore, frontend, and security checks; packaged images; deployed Cloud Run and Firebase Hosting; then verified the public site.

The root [README](../README.md) is the current user guide, local/Docker run book, deployment reference, and environment-variable guide. The root [architecture](../architecture.md) describes the deployed trust boundaries, persistence, authentication, and CI/CD flow.

## Required human record

The only remaining human-only evidence is a real non-team walkthrough. Before Moodle submission, have an outside person follow the public URL and record the result in [outside-user-test.md](outside-user-test.md). Do not substitute an automated test or invent a result.
