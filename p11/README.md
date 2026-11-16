# P11 Launch submission

**Score Companion · Team 08 · CMPS453 · Due November 16, 2026, 11:55 PM**

Score Companion is live at [music-companion-513717.web.app](https://music-companion-513717.web.app). Firebase Hosting provides the public HTTPS frontend and Cloud Run provides the Django/PDF-recognition API.

## Submission files

- [Final Word report](report/P11-Report.docx)
- [Final PDF report](report/P11-Report.pdf)
- [Official report template](P11-Report-template.docx)
- [Official grader notes](P11-grader-notes.docx)
- [Web-app launch guide](P11-WebApp-Launch-Guide.pdf)
- [Live launch screenshots](evidence/launch/README.md)
- [Team contribution record](team-contributions.md)
- [Outside-user test record](outside-user-test.md)

## Launch and CI/CD evidence

The protected-main deployment for commit `93e9de0` completed successfully in [GitLab pipeline 3072113477](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/pipelines/3072113477). It ran backend, Firestore, frontend, and security checks; packaged images; deployed Cloud Run and Firebase Hosting; then verified the public site.

The root [README](../README.md) is the current user guide, local/Docker run book, deployment reference, and environment-variable guide. The root [architecture](../architecture.md) describes the deployed trust boundaries, persistence, authentication, and CI/CD flow.

## Outside-user walkthrough

Ben Lopez, a person outside Team 08, completed the public walkthrough on November 14, 2026. The record includes the observed initial PDF-load delay, the follow-up allocation adjustment, and a successful retest in [outside-user-test.md](outside-user-test.md).
