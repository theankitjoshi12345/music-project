# Project Agent Instructions

## Issue tracking

- Use GitLab as the source of truth for project milestones and issues.
- Do not create, mirror, update, comment on, or otherwise manage GitHub issues
  unless the user explicitly requests GitHub issue work.
- GitLab remains the project tracker; GitHub must not be used for issue work.
  All repository files are mirrored between the two remotes.
- When a task changes GitLab milestones or issues, update `GITLAB_TRACKER.md`
  from the current GitLab data in the same task.
- Keep issue-level entries in `GITLAB_TRACKER.md` only for active milestones.
  When a milestone is achieved (closed), remove its associated issue entries
  from the tracker snapshot while retaining the milestone summary. Remove
  issue entries that have no milestone as well.
