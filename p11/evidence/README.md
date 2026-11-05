# P11 evidence

Record real observations with the date, deployed commit, environment, command or
user action, and result. Evidence must not contain tokens, session cookies,
client secrets, private PDFs, or personal test data.

- `launch/`: public browser screenshots, HTTPS/API/core-task results, and restart
  or redeployment persistence results.
- `ci-cd/`: successful GitLab pipeline and deployment job URLs and sanitized logs.
- `security/`: Django deployment checks, isolation tests, dependency scan results,
  response headers, and cloud access/billing configuration summaries.

The temporary free HTTPS demo, persistence restart, and two-session isolation
results are recorded under `launch/`. GitLab accepted the CI configuration but
blocked job execution until the account completes identity verification. Do not
relabel localhost, older P10 captures, or a blocked pipeline as successful launch
or CI evidence.
