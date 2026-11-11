import { useEffect, useState } from 'react'
import { AppLayout, ScreenHeading, LoadingSkeleton } from './components/score-companion'
import { mockUserHeaders, useMockSession } from './mockSession'
import { loadViewerData } from './pages/scoreViewerData'
import { ScoreImage } from './pages/PdfScoreReader'
import useMeasureKeyboard from './pages/useMeasureKeyboard'
import { adjacentMeasure } from './pages/measureNavigation'
import './MeasureMarker.css'

export default function MeasureMarker() {
  const { user } = useMockSession()
  const [data, setData] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [notes, setNotes] = useState({})
  const [retry, setRetry] = useState(0)
  const passages = data?.passages ?? []
  const selected = passages.find(passage => passage.id === selectedId) ?? passages[0]
  const previous = adjacentMeasure(passages, selected?.id, -1)
  const next = adjacentMeasure(passages, selected?.id, 1)
  useMeasureKeyboard(passages, selected?.id, passage => setSelectedId(passage.id))

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setData(null); setError('')
      try {
        const id = new URLSearchParams(window.location.hash.split('?')[1] || '').get('score')
        const result = await loadViewerData(id, controller.signal, fetch, mockUserHeaders(user))
        if (!controller.signal.aborted) { setData(result); setSelectedId(result.passages[0]?.id ?? null) }
      } catch (failure) { if (!controller.signal.aborted) setError(failure.message) }
    }
    load()
    return () => controller.abort()
  }, [user, retry])

  async function changePractice() {
    if (!selected) return
    setBusy(true); setError(''); setMessage('')
    const removing = selected.is_marked_for_practice
    try {
      if (removing && !selected.practice_mark_id) throw new Error('Reload this score to refresh its practice state.')
      const response = await fetch(removing ? `/api/practice-marks/${selected.practice_mark_id}/` : '/api/practice-marks/', {
        method: removing ? 'DELETE' : 'POST', headers: { 'Content-Type': 'application/json', ...mockUserHeaders(user) },
        ...(removing ? {} : { body: JSON.stringify({ passage_id: selected.id, note: notes[selected.id] || '' }) }),
      })
      if (!response.ok && !(removing && response.status === 404)) throw new Error('Your practice item could not be updated. Please try again.')
      const mark = removing ? null : await response.json()
      setData(current => ({ ...current, passages: current.passages.map(passage => passage.id === selected.id ? { ...passage, is_marked_for_practice: !removing, practice_mark_id: mark?.id ?? null, practice_note: mark?.note || '' } : passage) }))
      setMessage(`Measure ${selected.measure_number} ${removing ? 'and its note removed from' : 'saved for'} practice.`)
    } catch (failure) { setError(failure.message) }
    finally { setBusy(false) }
  }

  return <AppLayout className="measure-marker" activeHref="#/score-library" status="Measure marker" headingId="marker-title" busy={!data && !error}>
    <ScreenHeading id="marker-title" title="Select a measure to mark" subtitle="Choose a measure, read its notation, and save it for practice." />
    {!data && !error && <LoadingSkeleton kind="reader" label="Loading your score…" rows={2} />}
    {error && <div className="viewer-error" role="alert"><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Reload score</button></div>}
    {message && <p className="marker-message" role="status">{message}</p>}
    {data && !selected && <div className="empty-state"><h2>No measures ready yet</h2><p>Open a score in the reader to find its measures first.</p><a className="button-link" href={data.score ? `#/score-viewer?score=${data.score.id}` : '#/score-library'}>Open score reader →</a></div>}
    {selected && <>
      <p className="marker-score-title">{data.score.title}</p>
      <div className="marker-workspace">
        <aside className="marker-list" aria-label="Choose a measure">{passages.map(passage => <button className="button-secondary" key={passage.id} type="button" aria-current={passage.id === selected.id ? 'true' : undefined} onClick={() => setSelectedId(passage.id)}>Measure {passage.measure_number}<span>Page {passage.page_number}{passage.is_marked_for_practice ? ' · Saved' : ''}</span></button>)}</aside>
        <section className="marker-preview" aria-label="Selected measure">
          <h2>Measure {selected.measure_number} · Page {selected.page_number}</h2>
          {selected.practice_note && <aside className="saved-practice-note" aria-label="Saved practice note"><strong>Your practice note</strong><p>{selected.practice_note}</p></aside>}
          {!selected.is_marked_for_practice && <label className="practice-note">Practice note (optional)<textarea maxLength={500} value={notes[selected.id] || ''} onChange={event => setNotes(current => ({ ...current, [selected.id]: event.target.value }))} placeholder="What would you like to work on?" /></label>}
          <div className="screen-actions marker-actions"><button className="button-secondary" type="button" aria-label="Previous measure" disabled={!previous} onClick={() => setSelectedId(previous.id)}>← Previous</button><button className="button-secondary" type="button" aria-label="Next measure" disabled={!next} onClick={() => setSelectedId(next.id)}>Next →</button><button className={selected.is_marked_for_practice ? 'button-secondary' : 'button-primary'} type="button" disabled={busy} onClick={changePractice}>{busy ? 'Saving…' : selected.is_marked_for_practice ? 'Remove from practice' : 'Save for practice'}</button></div>
          {selected.preview_url ? <ScoreImage key={selected.id} src={selected.preview_url} alt={`Music notation for measure ${selected.measure_number}, page ${selected.page_number}`} /> : <p>Open the score reader to view the original notation.</p>}
          <a className="button-link" href={`#/score-viewer?score=${data.score.id}&passage=${selected.id}`}>Open this measure in the score reader →</a>
        </section>
      </div>
    </>}
  </AppLayout>
}
