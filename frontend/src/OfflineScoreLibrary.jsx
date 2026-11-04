import { useEffect, useState } from 'react'
import { AppLayout, ScreenHeading, LoadingSkeleton } from './components/score-companion'
import { mockUserHeaders, useMockSession } from './mockSession'
import './OfflineScoreLibrary.css'
import StudioArt from './components/score-companion/StudioArt'

const apiBase = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export default function OfflineScoreLibrary() {
  const { user } = useMockSession()
  const [parts, setParts] = useState(null)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [deletingId, setDeletingId] = useState(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setError(''); setParts(null)
      try {
        const response = await fetch(`${apiBase}/scores/`, { headers: mockUserHeaders(user), signal: controller.signal })
        if (!response.ok) throw new Error('Your library could not load. Please try again.')
        const data = await response.json()
        if (!Array.isArray(data)) throw new Error('The library returned an invalid response.')
        if (!controller.signal.aborted) setParts(data)
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure.message)
      }
    }
    load()
    return () => controller.abort()
  }, [user, retry])

  async function upload(event) {
    event.preventDefault()
    const form = event.currentTarget
    setUploading(true); setError(''); setMessage('')
    try {
      const response = await fetch(`${apiBase}/scores/upload/`, {
        method: 'POST', headers: mockUserHeaders(user), body: new FormData(form),
      })
      const score = await response.json()
      if (!response.ok) {
        const failure = score.score_file || score.page_count || score.detail
        throw new Error((Array.isArray(failure) ? failure[0] : failure) || 'The score could not be uploaded.')
      }
      window.location.assign(`#/score-viewer?score=${score.id}${score.source_file?.toLowerCase().endsWith('.pdf') ? '&extract=1' : ''}`)
    } catch (failure) { setError(failure.message) }
    finally { setUploading(false) }
  }

  async function deleteScore(score) {
    setDeletingId(score.id); setError(''); setMessage('')
    try {
      const response = await fetch(`${apiBase}/scores/${score.id}/`, { method: 'DELETE', headers: mockUserHeaders(user) })
      if (!response.ok && response.status !== 404) throw new Error('The score could not be deleted. Please try again.')
      setParts(current => current.filter(item => item.id !== score.id))
      setMessage(`${score.title}, its file, and its saved practice items were deleted.`)
    } catch (failure) { setError(failure.message) }
    finally { setDeletingId(null) }
  }

  return <AppLayout className="offline-library" activeHref="#/score-library" status="Library" headingId="library-title" busy={!parts && !error}>
    <div className="library-hero">
      <div><ScreenHeading id="library-title" byline="Your space to make music" title="Your score library" subtitle="Big pieces. Small steps. A little better every practice." />
        <ol className="library-steps"><li><span>1</span> Add your sheet music</li><li><span>2</span> Choose a measure</li><li><span>3</span> Save it for practice</li></ol>
      </div>
      <StudioArt />
    </div>
    <section className="offline-library__upload" aria-labelledby="upload-title">
      <div className="upload-intro"><span className="upload-icon" aria-hidden="true">＋</span><div><h2 id="upload-title">Add a score</h2><p>PDF or MusicXML · up to 10 MB</p></div></div>
      <form onSubmit={upload}>
        <label>Score file<input name="score_file" type="file" accept=".pdf,.musicxml,.xml,.mxl" required disabled={uploading} /></label>
        <button className="button-primary" type="submit" disabled={uploading}>{uploading ? 'Uploading…' : 'Add to library'}</button>
      </form>
    </section>
    {error && <div className="viewer-error" role="alert"><p>{error}</p>{!parts && <button type="button" onClick={() => setRetry(value => value + 1)}>Try again</button>}</div>}
    {message && <p className="library-message" role="status">{message}</p>}
    <section className="offline-library__parts" aria-labelledby="scores-title">
      <h2 id="scores-title">Scores {parts && <span>({parts.length})</span>}</h2>
      {!parts && !error && <LoadingSkeleton label="Loading your score library…" />}
      {parts?.length === 0 && <div className="empty-state"><h3>No scores yet</h3><p>Choose a file above to start. Your uploaded scores will appear here.</p></div>}
      {parts?.length > 0 && <ul className="library-list">{parts.map(score => <li className="offline-library__part" key={score.id}>
        <span className="library-score-icon" aria-hidden="true">♫</span><div className="library-score-info"><h3>{score.title}</h3><p>{score.page_count} {score.page_count === 1 ? 'page' : 'pages'} · {score.passage_count} measures{score.extraction_status === 'processing' ? ' · Finding measures…' : ''}</p></div>
        <div className="offline-library__part-actions screen-actions">
          <a className="button-primary" href={`#/score-viewer?score=${score.id}`}>Open score →</a>
          {score.source_file?.toLowerCase().endsWith('.pdf') && score.extraction_status === 'failed' && <a className="button-secondary" href={`#/score-viewer?score=${score.id}&extract=1`}>Retry conversion</a>}
          <details className="score-options"><summary>Score options</summary><div><a className="button-link" href={`#/measure-marker?score=${score.id}`}>Practice marker →</a><p>Delete this score, its uploaded file, and all attached practice items.</p><button className="button-danger" type="button" disabled={deletingId !== null || score.extraction_status === 'processing'} onClick={() => deleteScore(score)}>{deletingId === score.id ? 'Deleting…' : 'Delete score'}</button></div></details>
        </div>
      </li>)}</ul>}
    </section>
  </AppLayout>
}
