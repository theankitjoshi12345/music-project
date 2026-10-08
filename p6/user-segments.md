# P#6 User Segments

This segmentation uses the standardized interview transcripts as the evidence
source. Interview numbers refer to `Complete_Combined_Interview_Scripts_Standardized.txt`.
The P4 interview-summary table was used as a cross-check for the recurring
score-management pains; direct quotes below are copied from the transcripts.
All eight transcript entries were reviewed: Interviews 1–4 and 6–7 provide
musician workflows, while Interviews 5 and 8 provide ensemble-context
evidence. Participant names are intentionally omitted from this document.

## 1. Preparation-First Internalizers

### Segment Description

Preparation-First Internalizers reduce their dependence on the score during
rehearsal by memorizing material, mentally retaining corrections, and
practicing difficult passages until the response becomes automatic. Their main
need is enough time and a workable way to prepare before or between
run-throughs. Their pain is not necessarily navigation itself; it is the risk
of having to perform before they have had time to absorb difficult material or
multiple corrections.

This segment is meaningfully different from Reactive Score Annotators because
it primarily stores guidance in memory and practice rather than in persistent
score cues. It differs from Format-Constrained Score Navigators because a
particular file, screen, or page layout is not the defining source of friction.

### Supporting Evidence

- **Interview 2:** “No struggle, I memorize the music prior.”
- **Interview 1:** “Yeah. I remember it, and then I practice it the right way until it becomes muscle memory.”

### Why This Segment Matters

Personas from this segment can expose preparation-time and recall needs without
assuming that every musician wants more on-screen interaction. Their scenarios
should test how someone moves from receiving unfamiliar material or feedback to
being ready for the next rehearsal or performance.

## 2. Reactive Score Annotators

### Segment Description

Reactive Score Annotators use the score as an active external memory during
rehearsal. They add measure numbers, transition cues, rhythm reminders,
accidental marks, or emphasis when a passage is difficult or when rehearsal
feedback arrives. Their main need is to capture the right cue quickly and in
context, then find it again when it matters. Their pain is that rapid
rehearsal flow and attention to one correction can make it difficult to record
or apply the cue without losing readiness for the next passage.

This segment is defined by the annotation-and-recall workflow, not by whether
the score is paper or digital. It differs from Preparation-First Internalizers
because the score remains a working memory aid; it differs from
Format-Constrained Score Navigators because the central problem is preserving
musical context, not opening, locating, or visually reading a file.

### Supporting Evidence

- **Interview 7:** “I write the measure numbers on important spots and transitions. I also write ear-mapping signals over long multi-measure rests.”
- **Interview 6:** “Sometimes, on horn at least I will mark it if something’s flat so I don’t have to go through the mental problem.”

### Why This Segment Matters

This segment gives Logan, Ankit, and Jonathan a basis for personas whose
scenarios involve director callouts, difficult passages, transitions, or
repeated corrections. Resulting user stories can focus on keeping a cue tied to
the correct measure and retrieving it at the right moment.

## 3. Format-Constrained Score Navigators

### Segment Description

Format-Constrained Score Navigators spend rehearsal effort getting to, moving
through, or visually reading the score itself. Their workflow includes
downloading files for reliable access, searching folders for the correct part,
zooming or scrolling while playing, turning pages, scanning multi-page music,
or compensating for cramped and glare-prone displays. Their main needs are
reliable access, legible notation, and navigation that fits the performance
context. Their pain is the interruption or cognitive load created by the score
format and delivery system.

This segment is not “people who use tablets” or “people who use paper.” Some
interviewees described problems with both formats. It differs from Reactive
Score Annotators because the defining friction occurs before or while locating
and reading content, even when no annotation is needed. It differs from
Preparation-First Internalizers because it remains score-dependent in the
moment.

### Supporting Evidence

- **Interview 1:** “If you don't download it and you try to open it at the football games, you're not getting it. It's not happening.”
- **Interview 4:** “MuseScore doesn't have a good zoom functionality to it and the UI gets in the way of the notes. No markup either for finger positions.”

### Why This Segment Matters

This segment supports personas and scenarios centered on the live moment when
the score must be accessed, located, or read under rehearsal or performance
conditions. It keeps later user stories grounded in observed navigation and
readability behavior rather than assuming a preferred device or predetermined
solution.

## Segmentation Rationale

The interviews were grouped by the dominant way a musician manages the gap
between a score, rehearsal demands, and performance readiness: internalizing
the material through preparation, externalizing reminders in the score, or
navigating the score’s delivery and presentation constraints. The main
behavioral dimensions were (1) reliance on memory and advance practice versus
the score during rehearsal, (2) use of persistent annotations and cues, and
(3) the degree to which file access, page movement, layout, or readability
interrupts play.

The groups are intentionally not exclusive. For example, Interview 7 combines
cue-writing with later individual practice and uses both paper and tablet
workflows. Interview 1 prepares difficult passages and memorizes around page
turns, while also downloading files and scrolling during play. Interview 6
marks accidental information and also reports part-finding, zooming, and
folder-navigation friction. These overlaps are expected: they show that a
persona can be grounded in one dominant workflow while retaining relevant
secondary behaviors.

The director interviews provide context that readiness, self-diagnosis, and
readability matter in ensemble work, but they do not force a separate
director-based segment here. The three segments are grounded in repeated
interview behaviors and pains, not in a predefined product, demographic, or
instrument category.

## Requirement Check

- [x] Exactly three behavioral segments are defined.
- [x] Each segment has a descriptive name, description, and two traceable
  direct quotes.
- [x] Segments distinguish behaviors, needs, workflows, and pains rather than
  demographics.
- [x] Quotes are copied from the cited interview transcripts and participant
  names are omitted.
- [x] The rationale states grouping dimensions, overlap, and the absence of a
  predefined solution.
- [x] The document is structured for later persona, scenario, and user-story
  work.
