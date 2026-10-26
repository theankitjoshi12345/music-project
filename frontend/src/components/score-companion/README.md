# Shared Score Companion components

Import from `../components/score-companion` when building a page in `src/pages/`.
The entry point imports the shared stylesheet. Wrap screen content in
`AppLayout`: its `.score-companion` class scopes the shared styles so other
routes keep their existing appearance.

These components render UI and call callbacks. They do not fetch or save API
data, choose an owner, or implement screen-specific workflows. Each screen
keeps its own data loading and state. Score Viewer does this in
`src/pages/useScoreViewer.js`.

## Components and props

| Component | Main props | Purpose |
| --- | --- | --- |
| `AppLayout` | `status`, `activeHref`, `headingId`, `busy`, `children`, `navigation`, `className` | Header, responsive sidebar, and screen content region. `headingId` must match the screen heading's ID. |
| `AppHeader` | `status`, `homeHref` | Brand/home link and caller-supplied status text. |
| `SidebarNavigation` | `items`, `activeHref` | Navigation items shaped as `{ href, label }`; marks the active link with `aria-current`. |
| `ScreenHeading` | `id`, `title`, `subtitle`, `byline` | Screen title, optional supporting text and owner attribution. |
| `FeedbackPanel` | `title`, `children`, `actions`, `tone` | Loading/empty feedback (`tone="status"`, default) or an error (`tone="error"`). Pass action buttons as React nodes. |
| `ScoreContext` | `movement`, `instrument`, `sections`, `separator` | Consistent musical context; `sections` is an array of section names. |
| `ScoreNavigation` | `page`, `pageCount`, `onPageChange`, `sections`, `section`, `onSectionChange`, `context`, `measureRange` | Controlled previous/next and section controls. Page numbers are 1-based; buttons disable at boundaries. Callbacks receive the new page number or section name. |
| `ScoreSheet` | `heading`, `passages`, `label`, `notationLabel`, `emptyMessage`, `renderPassage` | Responsive passage grid and empty state. Each passage needs a stable `id`. Override `renderPassage(passage)` to supply a different cell. |
| `MeasurePreview` | `passage` | Non-interactive measure illustration using `section` and `measure_number`. Music notation is illustrative, not a real score renderer. |
| `MeasureJump` | `onJump` | Accessible measure-number form. Callback receives a number and returns an error string or an empty string on success. The form manages its own input/error state. |

## Basic page composition

This is an integration example, not a replacement for an owner's assigned screen:

```jsx
import {
  AppLayout, FeedbackPanel, ScreenHeading,
} from '../components/score-companion'

export default function ExamplePage({ loading, error, children }) {
  return (
    <AppLayout
      status="Practice review"
      activeHref="#/practice-review"
      headingId="review-title"
      busy={loading}
    >
      <ScreenHeading id="review-title" title="Practice review" />
      {loading && <FeedbackPanel>Loading saved passages…</FeedbackPanel>}
      {error && <FeedbackPanel tone="error">{error}</FeedbackPanel>}
      {!loading && !error && children}
    </AppLayout>
  )
}
```

## Extending the measure grid

Matthew can compose a measure preview with his own selection/marking control.
The selection state and API calls stay in his screen:

```jsx
<ScoreSheet
  heading="Movement I / Section B"
  passages={passages}
  renderPassage={(passage) => (
    <div>
      <MeasurePreview passage={passage} />
      <button type="button" onClick={() => selectPassage(passage.id)}>
        Select measure {passage.measure_number}
      </button>
    </div>
  )}
/>
```

Suggested adoption:

- Logan: layout, headings, and loading/error feedback for the score library.
- Matthew: score context, sheet, and measure preview with his own marking controls.
- Jonathan: layout, headings, context, and feedback for practice review.
- Ankit: layout, context, sheet, page/section controls, and measure jump.

Use truthful status labels. `AppHeader` displays the supplied text; it does not
detect offline file availability. Pass `Offline ready` only when the screen
has actually established that the score is cached and accessible offline.

Run `npm test` from `frontend/` for shared-component rendering and viewer data
tests. `npm run lint` and `npm run build` check the complete frontend.
