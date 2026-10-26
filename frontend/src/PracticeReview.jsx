import { useEffect, useState } from 'react'
import './PracticeReview.css'
import { scoreViewerHref } from './pages/scoreViewerData'

const apiBase = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

function MusicNoteIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 3v12.2a3.5 3.5 0 1 1-2-3.16V7.1l-8 1.6v8.5a3.5 3.5 0 1 1-2-3.16V7l12-2.4V3z" />
    </svg>
  )
}

async function responseJson(response) {
  if (!response.ok) {
    throw new Error(`Practice review request failed (${response.status}).`)
  }

  return response.json()
}

function PracticeReview() {
  const [marks, setMarks] = useState(null)
  const [error, setError] = useState('')
  const [savingId, setSavingId] = useState(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadMarks() {
      try {
        const response = await fetch(`${apiBase}/practice-marks/`, {
          signal: controller.signal,
        })
        const data = await responseJson(response)

        if (!Array.isArray(data)) {
          throw new Error('Practice review returned an invalid response.')
        }

        setMarks(data)
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setError(requestError.message)
        }
      }
    }

    loadMarks()
    return () => controller.abort()
  }, [])

  async function markResolved(mark) {
    setSavingId(mark.id)
    setError('')

    try {
      const response = await fetch(`${apiBase}/practice-marks/${mark.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_resolved: true }),
      })
      const updatedMark = await responseJson(response)

      setMarks((currentMarks) =>
        currentMarks.map((currentMark) =>
          currentMark.id === updatedMark.id ? updatedMark : currentMark,
        ),
      )
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSavingId(null)
    }
  }

  const firstMark = marks?.[0]
  const sharedContext =
    firstMark &&
    marks.every(
      (mark) =>
        mark.passage.movement === firstMark.passage.movement &&
        mark.passage.score_id === firstMark.passage.score_id &&
        mark.passage.section === firstMark.passage.section,
    )

  return (
    <div className="practice-review">
      <header className="practice-review__header">
        <a className="practice-review__brand" href="#/score-library">
          <MusicNoteIcon />
          <span>Score Companion</span>
        </a>
        <p className="practice-review__status">
          <span aria-hidden="true" />
          Offline ready
        </p>
      </header>

      <div className="practice-review__layout">
        <aside className="practice-review__sidebar">
          <nav aria-label="Score Companion">
            <a className="practice-review__nav-link" href="#/score-library">
              Score library
            </a>
            <a
              className="practice-review__nav-link is-active"
              href="#/practice-review"
              aria-current="page"
            >
              Practice review - Jonathan Dempsey
            </a>
          </nav>
        </aside>

        <main className="practice-review__content">
          <h1>Practice review</h1>
          <p className="practice-review__subtitle">
            Review saved passages, practice, then resolve.
          </p>

          {marks && (
            <section aria-labelledby="practice-review-summary">
              <h2 className="practice-review__summary" id="practice-review-summary">
                {marks.length} SAVED {marks.length === 1 ? 'MEASURE' : 'MEASURES'}
                {sharedContext &&
                  ` • ${firstMark.passage.movement.toUpperCase()} • SECTION ${firstMark.passage.section.toUpperCase()}`}
              </h2>

              {marks.length === 0 ? (
                <p className="practice-review__empty">
                  No saved practice measures yet.
                </p>
              ) : (
                <ul className="practice-review__list">
                  {marks.map((mark) => (
                    <li className="practice-review__item" key={mark.id}>
                      <article className="practice-review__card">
                        <p
                          className={`practice-review__state${mark.is_resolved ? ' is-resolved' : ''}`}
                        >
                          <span aria-hidden="true" />
                          {mark.is_resolved ? 'Resolved' : 'Unresolved'}
                        </p>
                        <h3>
                          {mark.passage.movement} — Measure {mark.passage.measure_number}
                        </h3>
                        {mark.note && <p className="practice-review__note">{mark.note}</p>}
                        <div className="practice-review__actions">
                          <a className="practice-review__button" href={scoreViewerHref(mark.passage)}>
                            Open passage <span aria-hidden="true">→</span>
                          </a>
                          <button
                            className="practice-review__button"
                            disabled={mark.is_resolved || savingId === mark.id}
                            onClick={() => markResolved(mark)}
                            type="button"
                          >
                            {savingId === mark.id
                              ? 'Saving…'
                              : mark.is_resolved
                                ? 'Resolved ✓'
                                : 'Mark resolved ✓'}
                          </button>
                        </div>
                      </article>
                      <p className="practice-review__footnote">
                        Your practice note stays attached to measure {mark.passage.measure_number}.
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}

          {!marks && !error && (
            <p className="practice-review__message" role="status">
              Loading practice review…
            </p>
          )}
          {error && (
            <p className="practice-review__error" role="alert">
              {error}
            </p>
          )}
        </main>
      </div>
    </div>
  )
}

export default PracticeReview
