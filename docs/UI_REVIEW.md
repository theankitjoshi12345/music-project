# Navigation and practice-data review

## User flow

The main flow is Library → Open score → Select a measure → Save for practice →
Practice review → Open measure. Library and Practice review stay in the shared
header on every screen. The score's options contain the separate Practice marker
and the destructive Delete score action.

| Finding | Change |
| --- | --- |
| Different headers and sidebars made routes feel disconnected | One shared header, active navigation and consistent demo-user selector |
| Every measure row had a competing save button | One practice action beside the selected notation; saved ticks remain in the list |
| Page arrows looked like measure navigation | Explicit Previous/Next measure buttons; page controls belong to Full page |
| Reaching measures on another page took extra steps | Global measure jump and left/right keys cross page boundaries automatically |
| Practice items had no removal action | Remove from practice in reader, marker and review; deletes the user-owned backend row and note |
| Loading replaced content with short messages or blank space | Accessible skeletons for library, reader, review, marker and notation requests |
| Score options overflowed on phones | Options expand inside the score card |
| The marker showed generic music illustrations for PDFs | The selected PDF measure uses its actual preview endpoint |

## Walkthrough and checks

`frontend/e2e/workflow.mjs` performs a browser walkthrough with a supplied real PDF
and an empty test library. It exercises the UI through its visible links and
controls. The benchmark PDF has two pages and recognizes 56 measures.

The walkthrough checks:

1. Upload a PDF, see the countdown tick, refresh without resetting its server
   start time, read the full page, and open notation after recognition completes.
2. Navigate with arrows and Previous/Next across a page boundary; stop at the
   first/last measure; type in the jump field without changing the selected
   measure until Go is pressed. Keyboard navigation keeps the reader in view.
3. Delay backend/image reads to observe skeletons. Fail an image request, retry,
   and recover. Fail a library read and recover through Try again.
4. Save a measure, resolve it, return to its exact page and measure, then remove
   it. A simulated failed DELETE keeps the item on the screen and in the API.
   Successful removal survives refresh and clears the passage's saved state.
5. Save again after removal and verify a new record with no retained note.
   Removing Alex's item preserves Sam's item; switching users shows the correct
   state. Removing Sam's own item leaves no test practice rows.
6. Reach Practice marker through Score options, view actual notation, move with
   keys, save/remove, and return to the same measure in the reader.
7. Check Library and Reader at widths 390, 768 and 1440 pixels, including open
   score options. Check nonempty Review and Marker on phone and desktop layouts.
   No horizontal page overflow is allowed.
8. Delete the disposable score and verify the original PDF returns 404 and all
   attached practice rows are gone. Capture screenshots; record no video.

These checks use headless Chrome and delayed/failed requests for specific failure
states. PDF recognition and normal API writes use the real backend. The workflow
requires no manual URL editing after its initial entry into the app. Screenshots
are kept in ignored tmp folders for visual inspection.

Both the native and Docker walkthroughs completed all tasks. The two-page PDF
produced 56 measures, keyboard navigation crossed the page boundary, every
removal remained correct after reload, and the tested layouts had no horizontal
overflow. The mobile score-options overflow found in the first pass was fixed
and the full walkthrough passed again. Backend checks also confirmed zero test
scores, passages, marks and PDFs after cleanup. There were no browser exceptions.
The primary flow now uses one selected-measure practice action and one shared
navigation bar, with a visible route back to Library from each screen.

## Storage semantics

A practice item is a PracticeMark database row containing its note and a link to
an existing Passage. Saving practice does not copy the uploaded PDF or create a
second notation file. DELETE removes that row and note. The reader gets the
current user's practice_mark_id and updates its saved state only after the server
confirms removal. Failed mutations retain the displayed record.

The score and passages stay available in Library after removing a practice item.
Delete score removes the source upload and cascades through its passages and all
users' practice marks. Tests use separate database/media storage and clean up
their own uploads; the regular local library is preserved.

See README for the isolated browser-test command and API_CONTRACT for ownership
and DELETE responses. The assessment covers the representative task flow and
tested viewport sizes; OMR accuracy and elapsed-time estimates still depend on
the score and host runtime.
