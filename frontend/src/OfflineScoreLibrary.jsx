import { useEffect, useState } from 'react'
import MockUserControl from './MockUserControl'
import { mockUserHeaders, useMockSession } from './mockSession'
import './OfflineScoreLibrary.css'
import { requestExtraction } from './pages/extractionRequest'

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
  const [deletingId, setDeletingId] = useState(null)
  const [extractingId, setExtractingId] = useState(null)

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
      if (!response.ok) {
        const failure = data.score_file || data.page_count || data.detail
        throw new Error((Array.isArray(failure) ? failure[0] : failure) || 'The score could not be uploaded.')
      }
      setParts((current) => [...(current || []).filter((part) => part.id !== data.id), data])
      setUploadMessage(data.already_uploaded ? 'This score is already in your library. Opening it now.' : data.extraction_status === 'complete'
        ? `${data.title} is saved and ${data.passage_count} measures were extracted. Open the score to mark a measure for Practice Review.`
        : `${data.title} is saved. Opening your score…`)
      form.reset()
      window.location.assign(`#/score-viewer?score=${data.id}${data.source_file?.toLowerCase().endsWith('.pdf') ? '&extract=1' : ''}`)
    } catch (uploadError) {
      setError(uploadError.message)
    } finally {
      setUploading(false)
    }
  }

  async function deleteScore(part) {
    setDeletingId(part.id)
    setError('')
    setUploadMessage('')
    try {
      const response = await fetch(`${apiBase}/scores/${part.id}/`, { method: 'DELETE', headers: mockUserHeaders(user) })
      if (!response.ok) throw new Error(`The score could not be deleted (${response.status}).`)
      setParts((current) => current.filter((item) => item.id !== part.id))
      setUploadMessage(`${part.title} and its saved practice marks were deleted.`)
    } catch (deleteError) {
      setError(deleteError.message)
    } finally {
      setDeletingId(null)
    }
  }

  async function extractMeasures(part) {
    setExtractingId(part.id)
    setError('')
    setUploadMessage('')
    try {
      await requestExtraction(part.id, mockUserHeaders(user))
      window.location.assign(`#/score-viewer?score=${part.id}`)
    } catch (extractError) {
      setError(extractError.message)
    } finally {
      setExtractingId(null)
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

      <main className="offline-library__content">
          <p className="library-kicker">YOUR REHEARSAL SPACE</p>
          <h1>Open a score. Stay in the music.</h1>
          <p className="offline-library__subtitle">
            Add a score once, then return to it whenever rehearsal starts.
          </p>

          <section className="offline-library__upload" aria-labelledby="upload-score-heading">
            <div><h2 id="upload-score-heading">Add a score</h2><p>Choose a PDF or MusicXML file from this device.</p></div>
            <form onSubmit={uploadScore}>
              <label>Score file<input name="score_file" type="file" accept=".pdf,.musicxml,.xml,.mxl,application/pdf,application/vnd.recordare.musicxml+xml" required /></label>
              <input name="instrument" type="hidden" value="" readOnly />
              <input name="page_count" type="hidden" value="1" readOnly />
              <button type="submit" disabled={uploading}>{uploading ? 'Adding…' : 'Add to library'}</button>
            </form>
            {uploadMessage && <p className="offline-library__upload-message" role="status">{uploadMessage}</p>}
          </section>

          <section className="offline-library__parts" aria-labelledby="downloaded-parts-heading">
            <h2 id="downloaded-parts-heading">Your scores</h2>
            {!parts && !error && <p className="offline-library__message" role="status">Loading your downloaded scores…</p>}
            {error && <p className="offline-library__message offline-library__message--error" role="alert">{error}</p>}
            {parts && parts.length === 0 && <p className="offline-library__message library-empty">No scores yet. Add one above, then open it here.</p>}
            {parts && parts.length > 0 && <ul>
              {parts.map((part) => (
                <li className="offline-library__part" key={part.id}>
                  <div className="offline-library__part-icon">
                    <MusicNoteIcon />
                  </div>
                  <div className="offline-library__part-details">
                    <h3>{part.title}</h3>
                    <p>{part.instrument} <span>·</span> {part.page_count} pages{part.extraction_status === 'complete' ? <> <span>·</span> {part.passage_count} measures detected</> : part.extraction_status === 'processing' ? <> <span>·</span> Extracting measures…</> : null}</p>
                  </div>
                  <div className="offline-library__part-actions"><a className="offline-library__open-button" href={`#/score-viewer?score=${part.id}`}>Open score <span aria-hidden="true">→</span></a>{part.source_file?.toLowerCase().endsWith('.pdf') && part.extraction_status !== 'complete' && <button className="offline-library__extract-button" type="button" disabled={extractingId !== null || part.extraction_status === 'processing'} onClick={() => extractMeasures(part)}>{extractingId === part.id || part.extraction_status === 'processing' ? 'Extracting…' : part.extraction_status === 'failed' ? 'Retry extraction' : 'Extract measures'}</button>}<button className="offline-library__delete-button" type="button" disabled={deletingId === part.id || extractingId === part.id || part.extraction_status === 'processing'} onClick={() => deleteScore(part)}>{deletingId === part.id ? 'Deleting…' : 'Delete score'}</button></div>
                </li>
              ))}
            </ul>}
          </section>
      </main>
    </div>
  )
}

export default OfflineScoreLibrary
