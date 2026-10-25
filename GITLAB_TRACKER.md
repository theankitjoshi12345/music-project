# GitLab Milestones and Issues

This document is a snapshot of the GitLab tracker for the Music Project,
retrieved on October 25, 2026 (Central Time). GitLab is the source of truth
for project milestones and issues.

- GitLab project: <https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project>
- Snapshot scope: all milestone summaries and issue-level entries for active milestones only.
- GitHub policy: GitHub is a repository mirror only. Do **not** create, mirror,
  or update GitHub issues or milestones.
- Retention policy: retain milestone summaries for all milestones. Remove
  issue-level entries when their milestone is closed, and remove entries for
  issues with no milestone.

## Active Milestones

### P#9 - Development Setup and First Commit

| Field | Value |
| --- | --- |
| GitLab ID | 7681221 |
| GitLab milestone | [!4](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/milestones/4) |
| Status | Active |
| Start date | Not set |
| Due date | October 26, 2026 |
| Description | Track P#9 development-environment setup, first screen implementations, and GitLab merge-request workflow. |
| Created / last updated (UTC) | 2026-10-24 02:18:53 / 2026-10-24 02:18:53 |
| Issues | 4 open; 1 closed |

| Issue | Owner | Status | Scope |
| --- | --- | --- | --- |
| [#24 Add Score Viewer & Navigation screen](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/work_items/24) | Ankit Joshi (`theankitjoshi12345`) | Open | Score Viewer & Navigation — hardest |
| [#25 Add Measure Marker screen](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/work_items/25) | Matthew Pisani (`p1sani2`) | Open | Measure Marker — hard |
| [#26 Add Practice Review screen](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/work_items/26) | J Demp (`JDemp06`) | Open | Practice Review — medium |
| [#27 Add Offline Score Library screen](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/work_items/27) | Logan Broussard (`lpb100`) | Open | Offline Score Library — easiest |
| [#28 Implement shared REST API contract](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/work_items/28) | Ankit Joshi (`theankitjoshi12345`) | Closed | Document and implement the shared Django REST API; closed by merged [MR !1](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/merge_requests/1) |

The four P#9 screen issues (#24–#27) require implementation from
`p9/Score_Companion_P8_Revised_Screens.pdf`, link directly to that PDF in
GitLab, and include the [Score Companion Figma design](https://www.figma.com/design/NSZliKsVC3CiwrjqQfrOHS).

Issue #24 is implemented on branch `24-score-viewer-navigation`, with page,
section, and measure navigation, live score/passages API reads, and a labeled
sample for an empty library. The issue remains open for browser verification
and teammate review in [draft MR !2](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/merge_requests/2)
before merging. The other screen issues remain open.

The #24 branch also provides shared frontend components and a usage guide in
`frontend/src/components/score-companion/` for the other screen owners.
Eleven frontend tests cover viewer data and shared-component rendering.

## Closed Milestones

### P#6 - Synthesizing Discovery

| Field | Value |
| --- | --- |
| GitLab ID | 7640834 |
| GitLab milestone | [!1](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/milestones/1) |
| Status | Closed |
| Start date | Not set |
| Due date | October 5, 2026 |
| Description | Not set |
| Created / last updated (UTC) | 2026-10-04 18:37:14 / 2026-10-05 19:53:06 |
| Issues | 0 open; 8 closed |

### P#7 - Rapid Prototyping

| Field | Value |
| --- | --- |
| GitLab ID | 7647560 |
| GitLab milestone | [!2](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/milestones/2) |
| Status | Closed |
| Start date | October 7, 2026 |
| Due date | October 12, 2026 |
| Description | Track the team’s evidence-based rapid-prototyping work: refined behavioral segments, critical moment, focused MVP features, static prototype screens, integration, README, and submission. |
| Created / last updated (UTC) | 2026-10-07 20:03:53 / 2026-10-21 23:22:52 |
| Issues | 0 open; 8 closed |

### P#8 - User Testing

| Field | Value |
| --- | --- |
| GitLab ID | 7661869 |
| GitLab milestone | [!3](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/milestones/3) |
| Status | Closed |
| Start date | Not set |
| Due date | October 19, 2026 |
| Description | Track P#8 usability-testing preparation, sessions, synthesis, design decisions, and final reporting. |
| Issues | 0 open; 7 closed |
| Closed / last updated (UTC) | 2026-10-19 23:44:36 |
