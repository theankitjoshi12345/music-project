# Project Agent Instructions

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
