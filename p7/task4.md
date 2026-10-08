# P#7 Task 4 - MVP Feature List

Copy each feature below into a matching **Part 3: MVP Feature List** table in the P#7 report template. Together, the five features support one rehearsal-to-practice flow: open the assigned score, reach the passage, capture the correction, retain its context, and practice the unresolved passage later.

## Feature 1 - Offline Score Library

**Description:** Store assigned score files locally in one predictable library so a musician can open the correct part without relying on a connection.

**Interview Insight:** “If you don't download it and you try to open it at the football games, you're not getting it. It's not happening.” - Interview 1

**Segment:** Format-Constrained Score Navigators.

**Problem Reduced:** The musician cannot reliably begin the rehearsal workflow when the assigned score is unavailable or difficult to find in shared storage.

**Assumption:** Musicians will download and organize their assigned parts before rehearsal or performance.

## Feature 2 - Uncluttered Score Viewer with Page and Section Navigation

**Description:** Display the selected score clearly and provide direct page or section controls for reaching the needed passage.

**Interview Insight:** “MuseScore doesn't have a good zoom functionality to it and the UI gets in the way of the notes. No markup either for finger positions.” - Interview 4

**Segment:** Format-Constrained Score Navigators.

**Problem Reduced:** Small or obstructed notation and awkward navigation can interrupt a musician before or during the corrected passage.

**Assumption:** Clear page and section controls can reduce navigation time enough to avoid disrupting performance.

## Feature 3 - One-Action Measure Marker

**Description:** Let a musician place a quick marker on the current measure while receiving a rehearsal correction.

**Interview Insight:** “Often we don’t have enough time to pick up our pencils, write it down, and get ready to play again.” - Interview 7

**Segment:** Reactive Score Annotators.

**Problem Reduced:** A complete note takes too much time during a rapid rehearsal cycle, but relying only on memory can lose the correction.

**Assumption:** A single, fast digital action can capture a useful reminder without causing the musician to miss the next entrance.

## Feature 4 - Measure-Linked Practice Cue

**Description:** Allow the musician to add a short cue to a marked measure after the immediate rehearsal pressure has passed.

**Interview Insight:** “I write the measure numbers on important spots and transitions. I also write ear-mapping signals over long multi-measure rests.” - Interview 7

**Segment:** Reactive Score Annotators.

**Problem Reduced:** A temporary mark alone may not explain what needs to change, while extensive notes can clutter the score.

**Assumption:** A concise, measure-linked cue gives enough context for later practice without obscuring notation.

## Feature 5 - Unresolved-Passage Review

**Description:** Show a focused list of marked measures and cues so the musician can select a passage, practice it, and mark it resolved.

**Interview Insight:** “Yeah. I remember it, and then I practice it the right way until it becomes muscle memory.” - Interview 1

**Segment:** Preparation-First Internalizers and Reactive Score Annotators.

**Problem Reduced:** Musicians need a focused way to turn rehearsal corrections into targeted individual practice instead of searching through the entire score or relying on memory.

**Assumption:** Musicians will return to unresolved markers and find the focused list more useful than a fully annotated score or memory alone.

## Features Not Included

| Feature | Why Excluded |
| --- | --- |
| Automatic score transcription or musical-error detection | It requires reliable audio or notation interpretation beyond the evidence-backed workflow and does not directly solve the immediate rehearsal-to-practice need. |
| Social feed or ensemble chat | No user story or interview insight identifies social communication as necessary for accessing, marking, or practicing the score. |
| Replacing every paper workflow | Interviews show that some musicians use paper or mixed workflows situationally; a blanket replacement would not fit the observed behaviors. |
