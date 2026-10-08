# P#6 — Synthesizing Discovery: Working Instructions

Use this guide before drafting, reviewing, or coordinating work for CMPS453
P#6. It is an execution guide, not a replacement for the course page or the
required report template.

## Authoritative information

- Current assignment deadline: **October 5, 2026, 11:55 PM**.
- Submission format: one PDF uploaded to Moodle.
- Start from the provided `report-template.docx` template when it is
  available.
- Use `RUBRIC.md` during review; it captures the supplied grader notes and
  identifies a scenario-count mismatch that needs careful handling.
- The pasted course page also contains March 2026 example dates. Those are
  stale examples and must not be used for this offering.
- GitLab is the task tracker. GitHub must not be used for issues.

## Team and responsibility boundaries

| Member | Name | P#6 responsibility |
| --- | --- | --- |
| A | Matthew | Team Lead: coordinates segments, features, assumptions, delivery schedule, and final report. No individual persona work is required. |
| B | Logan | Owns one complete persona → scenarios → user stories contribution. |
| C | Ankit | Owns one complete persona → scenarios → user stories contribution. |
| D | Jonathan | Owns one complete persona → scenarios → user stories contribution. |

## Safe operating rules

1. Treat interview notes and recordings as the only source for quotes,
   observations, behaviors, pains, and needs. Never invent a quote, a
   participant, or evidence. If supporting evidence is unavailable, mark that
   field `TODO — interview evidence needed`.
2. Preserve traceability: every persona must name a segment; every scenario
   must belong to that persona; every user story must follow from a scenario;
   every proposed feature must map back to one or more user stories.
3. Do not create, modify, assign, close, comment on, or otherwise manage a
   GitLab issue unless the user explicitly requests that exact tracker action.
4. Do not create or manage GitHub issues. GitHub is a code/document mirror;
   GitLab is the project tracker.
5. Do not submit, upload, convert, overwrite, or publish the final report
   without an explicit user request.
6. The user has explicitly authorized the project files, including the
   standardized interview source material, to be mirrored between GitHub and
   GitLab. Keep the material unchanged unless the user directs otherwise; do
   not add new raw transcripts, participant names, contact information, or
   identifying details without explicit authorization.
7. Do not change project code while preparing P#6 artifacts unless the user
   explicitly asks for a code change.
8. Before a GitLab push, inspect the outgoing commits and confirm that
   `GITLAB_TRACKER.md` is absent. That tracker snapshot is GitHub-only.

## Required report content

### 1. Title Page

- Product name
- Team number
- Member mapping (A–D) and names
- Identify Matthew (Member A) as Team Lead
- Date

### 2. Delivery Schedule

Include a table with component, owner, expected date, and delivered date. The
expected date must match the corresponding GitLab issue due date; the delivered
date is the date that issue was closed.

### 3. User Segments — Team

Define 2–3 behavioral—not demographic—segments. For each, provide:

- Descriptive behavioral name
- Description of shared behaviors, needs, or pain points
- One or two supporting interview quotes or observations

### 4. Individual Contributions — B, C, and D

Label every contribution with its member code, for example `Contributed by: B`.
Each member supplies one complete set:

- **Persona:** fictional name, segment, real interview quote, goals, pains,
  and behaviors
- **Scenarios:** one or two; each has trigger, context, goal, and current pain
- **User stories:** two to four; each uses exactly the form
  `As a [persona], I want to [action], so that [benefit].`

### 5. Feature List — Team

Combine all user stories into:

- Core Features: required to deliver product value
- Supporting Features: useful enhancements
- Excluded Features: explicitly out of scope, with a reason for each exclusion

### 6. Riskiest Assumptions — Team

Select exactly the top three. For each, state:

- The assumption
- Why it is risky (uncertainty and impact if false)
- How it could be tested (one practical validation method)

### 7. Final quality check

Before producing the PDF, verify:

- [ ] Every segment and persona is grounded in interview evidence.
- [ ] All individual contributions are labeled and complete.
- [ ] Scenarios and stories connect logically to their persona and segment.
- [ ] Features connect to stories; excluded features include a rationale.
- [ ] Exactly three meaningful, testable assumptions are present.
- [ ] Expected and delivered dates are consistent with GitLab.
- [ ] The document contains no raw interview transcripts or identifying data.
- [ ] The report is complete, readable, and exported as a PDF only when asked.

## Current tracker note

Matthew's individual persona issue is closed because the Team Lead does not
need to complete that individual contribution for this four-member team. Keep
the remaining tracker status unchanged unless the user explicitly directs a
GitLab action.

## Repository mirror policy

The user explicitly authorized the current project files to stay the same on
GitHub and GitLab on October 7, 2026. This includes
`p4/complete-combined-interview-scripts-standardized.txt`. The sole exception
is `GITLAB_TRACKER.md`, which remains GitHub-only and must never be staged or
pushed to GitLab.
