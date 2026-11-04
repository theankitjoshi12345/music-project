import { useEffect, useState } from 'react'
import { AppLayout, ScreenHeading, LoadingSkeleton } from './components/score-companion'
import { scoreViewerHref } from './pages/scoreViewerData'
import { mockUserHeaders, useMockSession } from './mockSession'
import './PracticeReview.css'

const apiBase = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export default function PracticeReview() {
  const { user } = useMockSession()
  const [marks, setMarks] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setMarks(null); setError('')
      try {
        const response = await fetch(`${apiBase}/practice-marks/`, { headers: mockUserHeaders(user), signal: controller.signal })
        if (!response.ok) throw new Error('Practice review could not load. Please try again.')
        const data = await response.json()
        if (!Array.isArray(data)) throw new Error('Practice review returned an invalid response.')
        if (!controller.signal.aborted) setMarks(data)
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure.message)
      }
    }
    load()
    return () => controller.abort()
  }, [user, retry])

  async function changeMark(mark, action) {
    setBusy({ id: mark.id, action }); setError(''); setMessage('')
    try {
      const removing = action === 'remove'
      const response = await fetch(`${apiBase}/practice-marks/${mark.id}/`, {
        method: removing ? 'DELETE' : 'PATCH',
        headers: { 'Content-Type': 'application/json', ...mockUserHeaders(user) },
        ...(removing ? {} : { body: JSON.stringify({ is_resolved: !mark.is_resolved }) }),
      })
      if (!response.ok && !(removing && response.status === 404)) throw new Error(removing ? 'This item could not be removed. Please try again.' : 'The practice status could not be saved. Please try again.')
      if (removing) {
        setMarks(current => current.filter(item => item.id !== mark.id))
        setMessage(`Measure ${mark.passage.measure_number} was removed from practice, including its saved note.`)
      } else {
        const updated = await response.json()
        setMarks(current => current.map(item => item.id === mark.id ? updated : item))
        setMessage(`Measure ${mark.passage.measure_number} ${updated.is_resolved ? 'marked practiced' : 'is ready to practice again'}.`)
      }
    } catch (failure) { setError(failure.message) }
    finally { setBusy(null) }
  }

  return <AppLayout className="practice-review" activeHref="#/practice-review" status="Practice review" headingId="review-title" busy={!marks && !error}>
    <ScreenHeading id="review-title" byline="A little practice, a lot of possibility" title="Practice review" subtitle={`This is ${user.name}'s practice list. Open a measure, give it a go, then mark it practiced.`} />
    <p className="review-help">Remove from practice deletes the saved item and its note. Your score stays in the library.</p>
    {error && <div className="viewer-error" role="alert"><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Reload review</button></div>}
    {message && <p className="review-message" role="status">{message}</p>}
    {!marks && !error && <LoadingSkeleton label="Loading practice review…" />}
    {marks?.length === 0 && <div className="empty-state"><h2>No saved practice measures yet</h2><p>Open a score and save a measure to build your practice list.</p><a className="button-link" href="#/score-library">Browse scores →</a></div>}
    {marks?.length > 0 && <section aria-labelledby="review-summary">
      <h2 id="review-summary" className="review-summary">{marks.length} saved {marks.length === 1 ? 'measure' : 'measures'}</h2>
      <ul className="practice-review__list">{marks.map(mark => <li key={mark.id}>
        <article className="practice-review__card" aria-label={`Practice measure ${mark.passage.measure_number}`} aria-busy={busy?.id === mark.id}>
          <div className="review-card-heading"><h3>{mark.passage.movement} — Measure {mark.passage.measure_number}</h3><span className={`review-state${mark.is_resolved ? ' is-resolved' : ''}`}>{mark.is_resolved ? '✓ Practiced' : 'To practice'}</span></div>
          <p className="review-location">Page {mark.passage.page_number} · {mark.passage.section}</p>
          {mark.note && <p className="practice-review__note">{mark.note}</p>}
          <div className="practice-review__actions screen-actions">
            <a className="button-primary" href={scoreViewerHref(mark.passage)}>Open measure →</a>
            <button className="button-secondary" type="button" disabled={busy !== null} onClick={() => changeMark(mark, 'resolve')}>{busy?.id === mark.id && busy.action === 'resolve' ? 'Saving…' : mark.is_resolved ? 'Practice again' : 'Mark practiced'}</button>
            <button className="button-danger review-remove" type="button" disabled={busy !== null} onClick={() => changeMark(mark, 'remove')}>{busy?.id === mark.id && busy.action === 'remove' ? 'Removing…' : 'Remove from practice'}</button>
          </div>
        </article>
      </li>)}</ul>
    </section>}
  </AppLayout>
}
