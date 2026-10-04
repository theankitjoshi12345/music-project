# Project Agent Instructions

## P#6 work

- Before performing any P#6 work, read `P6_INSTRUCTIONS.md` and
  `P6_RUBRIC.md`; follow their evidence, privacy, tracker, publication, and
  review boundaries.
- When the user explicitly requests publication of all pending project files,
  inspect `git status`, state any public-repository privacy implications, then
  commit and push every listed pending file to the `github` remote only. Do
  not push those files to GitLab unless the user separately asks.

## Issue tracking

- Use GitLab as the source of truth for project milestones and issues.
- Do not create, mirror, update, comment on, or otherwise manage GitHub issues
  unless the user explicitly requests GitHub issue work.
- The GitHub repository is a code mirror; GitLab remains the project tracker.
- When a task changes GitLab milestones or issues, update `GITLAB_TRACKER.md`
  from the current GitLab data in the same task.
- `GITLAB_TRACKER.md` is GitHub-only. It must never be staged or pushed to the
  GitLab `origin` remote, even though it is tracked in the GitHub-only history.
- `.gitignore` prevents the tracker from being newly added on a GitLab-based
  branch; it does not protect an already tracked copy. Before any GitLab push,
  inspect the outgoing commit(s) and confirm that the tracker is absent.
