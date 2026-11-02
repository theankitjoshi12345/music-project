import { useEffect, useState } from 'react'
import MockUserControl from './MockUserControl'
import { mockUserHeaders, useMockSession } from './mockSession'
import './OfflineScoreLibrary.css'

const apiBase = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

function MusicNoteIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 3v12.2a3.5 3.5 0 1 1-2-3.16V7.1l-8 1.6v8.5a3.5 3.5 0 1 1-2-3.16V7l12-2.4V3z" />
    </svg>
  )
}

function OfflineScoreLibrary() {
  const { user } = useMockSession()
  const [parts, setParts] = useState(null)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    async function loadParts() {
      try {
        setError('')
        const response = await fetch(`${apiBase}/scores/`, {
          headers: mockUserHeaders(user),
          signal: controller.signal,
        })
        if (!response.ok) throw new Error(`The score library could not load (${response.status}).`)
        const data = await response.json()
        if (!Array.isArray(data)) throw new Error('The score library returned an invalid response.')
        setParts(data.filter((part) => part.available_offline))
      } catch (loadError) {
        if (loadError.name !== 'AbortError') setError(loadError.message)
      }
    }
    loadParts()
    return () => controller.abort()
  }, [user])

  async function uploadScore(event) {
    event.preventDefault()
    const form = event.currentTarget
    const file = form.elements.score_file.files[0]
    if (!file) {
      setError('Choose a PDF, MusicXML, XML, or MXL score file first.')
      return
    }
    setUploading(true)
    setError('')
    setUploadMessage('')
    try {
      const response = await fetch(`${apiBase}/scores/upload/`, {
        method: 'POST',
        headers: mockUserHeaders(user),
        body: new FormData(form),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.score_file?.[0] || data.page_count?.[0] || 'The score could not be uploaded.')
      setParts((current) => [...(current || []), data])
      setUploadMessage(`${data.title} is saved to your offline library.`)
      form.reset()
    } catch (uploadError) {
      setError(uploadError.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="offline-library">
      <header className="offline-library__header">
        <a className="offline-library__brand" href="#/score-library">
          <MusicNoteIcon />
          <span>Score Companion</span>
        </a>
        <p className="offline-library__status">
          <span aria-hidden="true" />
          Offline ready
        </p>
        <MockUserControl />
      </header>

      <div className="offline-library__layout">
        <aside className="offline-library__sidebar">
          <nav aria-label="Score Companion">
            <a className="offline-library__nav-link is-active" href="#/score-library" aria-current="page">
              Score library
            </a>
            <a className="offline-library__nav-link" href="#/practice-review">
              Practice review
            </a>
          </nav>
        </aside>

        <main className="offline-library__content">
          <h1>Your offline score library</h1>
          <p className="offline-library__subtitle">
            Select a score saved for {user.name}'s rehearsal.
          </p>

          <section className="offline-library__upload" aria-labelledby="upload-score-heading">
            <div><h2 id="upload-score-heading">Add a score</h2><p>Upload a PDF or MusicXML score to add it to this local library.</p></div>
            <form onSubmit={uploadScore}>
              <label>Score file<input name="score_file" type="file" accept=".pdf,.musicxml,.xml,.mxl,application/pdf,application/vnd.recordare.musicxml+xml" required /></label>
              <label>Instrument<input name="instrument" placeholder="e.g. Clarinet" /></label>
              <label>Pages<input name="page_count" type="number" min="1" defaultValue="1" /></label>
              <button type="submit" disabled={uploading}>{uploading ? 'Uploading…' : 'Upload score'}</button>
            </form>
            {uploadMessage && <p className="offline-library__upload-message" role="status">{uploadMessage}</p>}
          </section>

          <section className="offline-library__parts" aria-labelledby="downloaded-parts-heading">
            <h2 id="downloaded-parts-heading">Your downloaded parts</h2>
            {!parts && !error && <p className="offline-library__message" role="status">Loading your downloaded scores…</p>}
            {error && <p className="offline-library__message offline-library__message--error" role="alert">{error}</p>}
            {parts && parts.length === 0 && <p className="offline-library__message">No scores are available offline for this demo user yet.</p>}
            {parts && parts.length > 0 && <ul>
              {parts.map((part) => (
                <li className="offline-library__part" key={part.id}>
                  <div className="offline-library__part-icon">
                    <MusicNoteIcon />
                  </div>
                  <div className="offline-library__part-details">
                    <h3>{part.movement} — {part.instrument}</h3>
                    <p>{part.title} <span>·</span> {part.page_count} pages <span>·</span> Available offline</p>
                  </div>
                  <a className="offline-library__open-button" href={`#/score-viewer?score=${part.id}`}>
                    Open score <span aria-hidden="true">→</span>
                  </a>
                </li>
              ))}
            </ul>}
          </section>
        </main>
      </div>
    </div>
  )
}

export default OfflineScoreLibrary
