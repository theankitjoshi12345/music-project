import { useEffect, useRef, useState } from 'react'
import { initialPage, loadViewerData, pagePassages, samplePassages, sampleScore, sectionOptions } from './scoreViewerData'
import './ScoreViewer.css'

function Measure({ passage }) {
  return (
    <article className="viewer-measure" aria-label={'Section ' + passage.section + ', measure ' + passage.measure_number}>
      <span className="viewer-measure-label">m. {passage.measure_number}</span>
      <div className="viewer-staff" aria-hidden="true">
        <i /><i /><i /><i /><i />
        <b className="viewer-note note-one" /><b className="viewer-note note-two" />
        <b className="viewer-note note-three" /><b className="viewer-note note-four" />
      </div>
    </article>
  )
}

export default function ScoreViewer() {
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  const [jump, setJump] = useState('')
  const [jumpError, setJumpError] = useState('')
  const [location, setLocation] = useState(window.location.hash)
  const jumpField = useRef(null)

  useEffect(() => {
    const updateLocation = () => setLocation(window.location.hash)
    window.addEventListener('hashchange', updateLocation)
    return () => window.removeEventListener('hashchange', updateLocation)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError('')
      setData(null)
      setJumpError('')
      const scoreId = new URLSearchParams(location.split('?')[1] || '').get('score')
      try {
        const result = await loadViewerData(scoreId, controller.signal)
        if (!controller.signal.aborted) {
          setData(result)
          setPage(initialPage(result.passages, result.score.page_count))
        }
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure.message || 'Unable to load the score.')
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    load()
    return () => controller.abort()
  }, [location, retry])

  const score = data?.score
  const passages = data?.passages ?? []
  const visible = pagePassages(passages, page)
  const sections = sectionOptions(passages)
  const currentSections = sectionOptions(visible)
  const section = currentSections[0] ?? ''
  const context = score ? score.movement + ' • ' + score.instrument : ''
  const measureRange = visible.length ? 'Measures ' + visible[0].measure_number + '–' + visible.at(-1).measure_number : 'No measures on this page'

  function changePage(value) {
    setPage(value)
    setJumpError('')
  }

  function jumpToMeasure(event) {
    event.preventDefault()
    const match = passages.find((passage) => passage.measure_number === Number(jump))
    if (!match) {
      setJumpError('Enter a measure number available in this score.')
      jumpField.current?.focus()
      return
    }
    changePage(match.page_number)
  }

  return (
    <main className="score-viewer">
      <header className="score-topbar">
        <a className="viewer-brand" href="#/score-library"><span aria-hidden="true">♫</span> Score Companion</a>
        <span className="viewer-status"><i /> {data?.isSample ? 'Sample score' : 'Score viewer'}</span>
      </header>
      <div className="viewer-layout">
        <aside className="score-sidebar" aria-label="Main navigation">
          <a href="#/score-library">Score library</a>
          <a href="#/practice-review">Practice review</a>
        </aside>
        <section className="score-content" aria-labelledby="score-title" aria-busy={loading}>
          <header className="score-heading">
            <p className="viewer-byline">Score viewer & navigation · Ankit Joshi</p>
            <h1 id="score-title">{score ? score.movement + ' — ' + score.instrument : 'Your score'}</h1>
            <p>{score ? (score.title === score.movement ? 'Find your place. Pick up where rehearsal left off.' : score.title) : 'Open a part and find your place.'}</p>
          </header>

          {loading && <p role="status" className="viewer-message">Loading your score…</p>}
          {error && <section className="viewer-message" role="alert">
            <h2>We couldn’t open this score</h2><p>{error}</p>
            <button type="button" onClick={() => setRetry((value) => value + 1)}>Try again</button>
            <button type="button" onClick={() => {
              setData({ score: sampleScore, passages: samplePassages, isSample: true })
              setPage(2)
              setError('')
            }}>View sample score</button>
          </section>}

          {score && <>
            {data.isSample && <p className="viewer-sample">Sample score · No downloaded scores yet. This preview is not saved to your library.</p>}
            <section className="score-controls" aria-label="Score navigation">
              <div className="score-context">{context}{currentSections.length > 0 && ' • Section ' + currentSections.join(', ')}</div>
              <div className="viewer-toolbar">
                <div className="navigation-row">
                  <button type="button" onClick={() => changePage(page - 1)} disabled={page <= 1}>‹ Previous</button>
                  <strong aria-live="polite">Page {page} of {score.page_count}</strong>
                  <button type="button" onClick={() => changePage(page + 1)} disabled={page >= score.page_count}>Next ›</button>
                </div>
                {sections.length > 0 && <label className="viewer-section-picker">Section
                  <select aria-label="Jump to section" value={section} onChange={(event) => changePage(passages.find((item) => item.section === event.target.value).page_number)}>
                    {!section && <option value="">Choose section</option>}
                    {sections.map((name) => <option key={name} value={name}>Section {name}</option>)}
                  </select>
                </label>}
              </div>
              <p className="viewer-measure-range" aria-live="polite">{measureRange}</p>
            </section>

            <section className="score-sheet" aria-label={'Score page ' + page}>
              <div className="viewer-sheet-heading">
                <h2>{context}{currentSections.length > 0 && ' / Section ' + currentSections.join(', ')}</h2>
                <span>Illustrative notation</span>
              </div>
              {visible.length > 0 ? <div className="viewer-measure-grid">{visible.map((passage) => <Measure key={passage.id} passage={passage} />)}</div>
                : <p className="viewer-empty">No measures have been added for this page yet. Try another page or section.</p>}
            </section>
            <div className="viewer-bottom-row">
              <form className="viewer-jump" onSubmit={jumpToMeasure}>
                <label htmlFor="viewer-jump-measure">Go to measure</label>
                <input ref={jumpField} id="viewer-jump-measure" type="number" min="1" step="1" required value={jump} onChange={(event) => setJump(event.target.value)} aria-invalid={Boolean(jumpError)} aria-describedby={jumpError ? 'viewer-jump-error' : undefined} placeholder="e.g. 24" />
                <button type="submit">Go →</button>
              </form>
              <p className="viewer-hint">Your place, at a glance. Use the page controls or jump to a section.</p>
            </div>
            {jumpError && <p id="viewer-jump-error" className="viewer-error" role="alert">{jumpError}</p>}
          </>}
        </section>
      </div>
    </main>
  )
}
