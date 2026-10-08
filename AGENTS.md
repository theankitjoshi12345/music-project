# Project Agent Instructions

## P#6 work

- Before performing any P#6 work, read `p6/INSTRUCTIONS.md` and
  `p6/RUBRIC.md`; follow their evidence, privacy, tracker, publication, and
  review boundaries.
- Keep project files synchronized between the `github` and GitLab `origin`
  remotes. The sole file exception is `GITLAB_TRACKER.md`, which is
  GitHub-only and must never be staged or pushed to GitLab.
- When the user explicitly requests publication of all pending project files,
  inspect `git status`, state any public-repository privacy implications, then
  commit and push every eligible listed file to both remotes. Confirm that
  `GITLAB_TRACKER.md` is excluded from the GitLab commit before pushing.

## Issue tracking

- Use GitLab as the source of truth for project milestones and issues.
- Do not create, mirror, update, comment on, or otherwise manage GitHub issues
  unless the user explicitly requests GitHub issue work.
- GitLab remains the project tracker; GitHub must not be used for issue work.
  Repository files, other than `GITLAB_TRACKER.md`, are mirrored between the
  two remotes.
- When a task changes GitLab milestones or issues, update `GITLAB_TRACKER.md`
  from the current GitLab data in the same task.
- `GITLAB_TRACKER.md` is GitHub-only. It must never be staged or pushed to the
  GitLab `origin` remote, even though it is tracked in the GitHub-only history.
- `.gitignore` prevents the tracker from being newly added on a GitLab-based
  branch; it does not protect an already tracked copy. Before any GitLab push,
  inspect the outgoing commit(s) and confirm that the tracker is absent.
