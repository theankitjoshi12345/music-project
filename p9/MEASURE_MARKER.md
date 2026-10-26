# Measure Marker — issue 25

Open http://localhost:5173/#/measure-marker after running npm ci and npm run dev in frontend.

Implements the selection and independent saved-measure states from revised design pages 7, 8 and 10. The score uses illustrative SVG notation matching the reference; it is not a PDF renderer.

## Documented mock data
This screen intentionally uses the issue's documented-mock-data option. Eight local Passage objects represent Section B, page 2, measures 17–24. Each includes id, section, measure_number, page_number and is_marked_for_practice matching GET /scores/{id}/passages/. IDs 17–24 are demo IDs only. Saved IDs persist under score-companion-measure-marker-demo-v1 in localStorage. Browser storage failure is reported without showing an unsaved mark as saved. No server requests are made, and these local marks do not populate the teammate's Practice Review screen.

Future API integration should load actual passage IDs from GET /scores/{id}/passages/ and POST {passage_id, note} to /practice-marks/, updating saved state only after success. Do not submit demo IDs to the backend.

## Manual verification
- Initially the save action is disabled. Tab to a measure and press Enter or Space to select it.
- Select 24 and save: count becomes one and a SAVED label appears.
- Select 20: 24 remains saved and 20 shows SELECTED. Save: count becomes two.
- Select a saved measure: the save action is disabled and the count remains unchanged.
- Reload: saved measures remain saved.
- Check widths of 375px and 1280px: grid becomes two/four columns and navigation remains usable.
- Check keyboard focus and status announcements. Selection and saving use text labels as well as colors.

Only App.jsx routing and the new MeasureMarker component/styles are involved. Teammate screen implementations are untouched. Obtain teammate review before merging; use Closes #25 in the merge request.
