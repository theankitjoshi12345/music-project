# P10 Integrated MVP One Hour Plan

## Goal

Deliver one locally runnable Score Companion journey on `main` that proves the
four P9 screens work as one product. The journey starts in the Offline Score
Library, opens a score, marks a practice passage, and finishes by reviewing or
resolving that passage. The app must make the active mock user visible wherever
data is user-specific.

## Timebox and working rules

Complete the work within one hour of the P10 kickoff. Each contributor works
on a feature branch, opens a merge request, requests review, and merges only
after the target path still works on current `main`. Keep changes small enough
to review quickly. Do not add production authentication, secrets, or services.

## Shared decisions to make first

1. Use one mock-auth approach for the whole app: a fixed development user or a
   small user switcher. Put the active-user state in one shared module or
   context rather than reimplementing it per screen.
2. Treat the shared journey as: Library → Score Viewer → Measure Marker →
   Practice Review → Score Viewer. Every handoff must carry a valid score or
   passage identifier.
3. Keep the golden-path data shape consistent across frontend and API work:
   `user`, `score`, `passage`, and `practiceMark`. Document the fields the
   journey needs in `API_CONTRACT.md` or a linked companion file.

## Work slices

| Owner | Slice | Done when |
| --- | --- | --- |
| Ankit | Shared mock user, data contract, and path integration | A single source of active-user state exists; IDs and route parameters match the contract; the full journey can be run on `main`. |
| Logan | Library entry and viewer handoff | A user can choose a score in the library and reach the correct score in the viewer without a broken or placeholder control. |
| Matthew | Marker creation and review handoff | A selected measure becomes a user-scoped practice mark and the user can continue to its review context. |
| Jonathan | Practice-review completion loop | Review displays the shared mark for the active user, supports its intended status action, and links back to the original score or passage. |
| Team | Reliability, evidence, and report | README supports a fresh local run; smoke test and clean-clone evidence are recorded; the P10 report includes screenshots, MRs, integration notes, demo script, and honest AI-use examples. |

## Acceptance checklist

- [ ] The report has a one-paragraph golden path with a start state and success state.
- [ ] Mock auth is named and explained in the README; changing users changes user-scoped data where applicable.
- [ ] All golden-path controls work end to end on `main`.
- [ ] The data contract lists the entities and fields used by the journey.
- [ ] Each member has a meaningful merged merge request or a documented equivalent.
- [ ] README instructions cover clone, dependencies, backend, frontend, mock auth, and the `main` branch.
- [ ] One teammate performs a clean-clone check and records the result and any README fix.
- [ ] The report captures integration points, issues resolved, testing, screenshots, demo details, Git activity, and AI use.

## Final ten minutes

1. Merge the reviewed slices and run the frontend tests, lint, build, Django tests, and a manual golden-path smoke test.
2. Verify the journey with the chosen mock user; if user switching is included, verify the user-specific behavior once more.
3. Fill the P10 report template with links, screenshots, owners, and dates that match the repository.
4. Run from the README in a clean checkout or document any gap immediately.
5. Record the 1–2 minute demo script and a fallback if the live run fails.

## Evidence standards

Use only behavior that exists in the repository. Describe partial work plainly,
link every merge request, and keep screenshots tied to the golden path. The
report should make it easy to reproduce the local run and to trace each member
contribution.
