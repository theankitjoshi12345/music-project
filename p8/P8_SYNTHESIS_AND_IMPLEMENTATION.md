# Score Companion - P#8 Synthesis and Implementation Plan

**Decision date:** October 18, 2026
**Study status:** Testing concluded at three participants by team decision. No additional participants will be recruited.

## Evidence inventory

| Participant | Segment | Source | Completion | Time |
| --- | --- | --- | ---: | ---: |
| Participant 1 | Format-Constrained Score Navigator | Jonathan's supplied observation PDF | Yes | 2 minutes |
| Participant 2 | Reactive Score Annotator | Jonathan's supplied observation PDF | Yes | 1.5 minutes |
| Participant 3 | Musician using a tablet before practice | Logan's GitLab issue #19 session note | Yes, with confusion | Not recorded |

The study is a small, formative Wizard-of-Oz test. The records substantiate task behavior and reactions, but not all observer/facilitator attendance details or exact timestamps were recorded. Findings are therefore directional rather than statistically generalizable.

## Cross-session pattern analysis

### P1 - Score representation and visual context are insufficient

Participants 1 and 2 both asked for measures that look more like sheet music. Participant 1 said the view did not look like normal sheet music, and Participant 2 found the experience empty. Participant 1 also lacked the song context needed to interpret “unresolved passages.” This is repeated feedback from two of three participants, so it is the highest-priority credibility and comprehension problem.

### P2 - Saving and reviewing corrections has an unclear mental model

Participant 1 did not know to use **Practice review** after saving. Participant 2 attempted review before saving and asked whether they were adding a correction or merely saving measures. Participant 3 did not understand the marker icon and initially navigated back to the library. All three reveal uncertainty about the relationship among marker, cue, saved passage, and review.

### P3 - Current copy is too narrow for the intended rehearsal workflow

Participant 3 found “add context after rehearsal” inconsistent with using the app before rehearsal. Participant 2 also wanted a clearer prompt while adding a practice note. The cue flow needs neutral timing language and explicit instructions.

### P4 - Offline access and completion feedback should be retained

Participant 3 explicitly valued the offline-ready indicator. The same participant found the large resolved check motivating; Participants 1 and 2 also completed the core flow. These elements support the product’s central promise and should remain.

### P5 - Value is not yet differentiated enough

Participants 1 and 2 said they would not use the prototype in its current state: it felt convoluted, not interactive enough, or not different enough. Participant 2 suggested a tuner or metronome. Those tools are useful ideas but are not included in the next iteration because they do not resolve the core score-marking comprehension failure.

## Implementation decisions

| Priority | Decision | Evidence | Acceptance check |
| --- | --- | --- | --- |
| P0 | Replace placeholder measure blocks with a legible, realistic score excerpt, persistent piece/movement title, and measure/section context in review. | P1, P2 | A tester can identify the current piece, section, and marked measure without asking what it refers to. |
| P0 | Turn the star into a labeled **Mark for practice** control; after activation, show the selected measure and an explicit **Add note** / **Review saved passages** next step. | P1, P2, P3 | A tester can explain what was saved and reach its review from the confirmation state. |
| P1 | Replace “add context after rehearsal” with “Add a practice note now or later,” and show an example note prompt. | P2, P3 | A tester understands that a cue may be added before, during, or after rehearsal. |
| P1 | Support repeated marking in the score view and display a marked-count indicator. | P3 | A tester can mark two measures and see both reflected in review. |
| P2 | Retain the offline-ready badge and resolved confirmation, while pairing the latter with a concise next action. | P3 | Offline availability and successful resolution are visible without obscuring the score task. |
| Deferred | Do not add tuner, metronome, social features, or AI correction detection in this iteration. | P2; MVP scope | Core score-to-review flow is comprehensible before scope expansion. |

## Build sequence

1. Update the score-view and review screens with real-looking notation and musical context.
2. Implement the explicit mark, note, and review states with clear labels.
3. Add repeatable multi-measure marking and marked-count feedback.
4. Conduct a future validation round focused on first-use comprehension of marking and review.

## Traceability

- Participant 1 and Participant 2 evidence: `P8_TwoParticipants_Issues2-4.pdf`.
- Participant 3 evidence: `LOGAN_GITLAB_SESSION.md`, downloaded from GitLab issue #19.
- Existing prototype under test: `Score Companion - P8 User Testing Prototype - Figma.pdf`.

This document intentionally uses anonymous participant identifiers only.
