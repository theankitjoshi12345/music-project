import { useEffect, useState } from 'react'
import MockUserControl from './MockUserControl'
import { mockUserHeaders, useMockSession } from './mockSession'
import './MeasureMarker.css'

const apiBase = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

function selectedScoreId() {
  return new URLSearchParams(window.location.hash.split('?')[1] || '').get('score')
}

function Staff() {
  return <svg viewBox="0 0 220 70" aria-hidden="true">
    {[25, 35, 45, 55, 65].map((y) => <line key={y} x1="0" x2="220" y1={y} y2={y} stroke="#91a5ba" />)}
    {[[32, 45], [67, 55], [102, 65], [137, 45]].map(([x, y]) => <g key={x}><ellipse cx={x} cy={y} rx="7" ry="5" fill="currentColor" /><line x1={x + 6} x2={x + 6} y1={y} y2={y - 35} stroke="currentColor" /></g>)}
  </svg>
}

export default function MeasureMarker() {
  const { user } = useMockSession()
  const [score, setScore] = useState(null)
  const [passages, setPassages] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const selected = passages?.find((passage) => passage.id === selectedId)
  const count = passages?.filter((passage) => passage.is_marked_for_practice).length ?? 0

  useEffect(() => {
    const controller = new AbortController()
    async function loadMarker() {
      try {
        setError('')
        setMessage('')
        setSelectedId(null)
        setPassages(null)
        const headers = mockUserHeaders(user)
        const scoresResponse = await fetch(`${apiBase}/scores/`, { headers, signal: controller.signal })
        if (!scoresResponse.ok) throw new Error(`The score library could not load (${scoresResponse.status}).`)
        const scores = await scoresResponse.json()
        const requestedId = selectedScoreId()
        const activeScore = scores.find((item) => String(item.id) === requestedId) ?? scores.find((item) => item.available_offline) ?? scores[0]
        if (!activeScore) throw new Error('Add a score in the library before marking a measure.')
        const passagesResponse = await fetch(`${apiBase}/scores/${activeScore.id}/passages/`, { headers, signal: controller.signal })
        if (!passagesResponse.ok) throw new Error(`The score passages could not load (${passagesResponse.status}).`)
        const data = await passagesResponse.json()
        if (!Array.isArray(data)) throw new Error('The score passages returned an invalid response.')
        setScore(activeScore)
        setPassages(data)
      } catch (loadError) {
        if (loadError.name !== 'AbortError') setError(loadError.message)
      }
    }
    loadMarker()
    return () => controller.abort()
  }, [user])

  async function save() {
    if (!selected || selected.is_marked_for_practice) return
    setSaving(true)
    setError('')
    try {
      const response = await fetch(`${apiBase}/practice-marks/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...mockUserHeaders(user) },
        body: JSON.stringify({ passage_id: selected.id }),
      })
      if (!response.ok) throw new Error(`Could not save this measure (${response.status}).`)
      setPassages((current) => current.map((passage) => passage.id === selected.id ? { ...passage, is_marked_for_practice: true } : passage))
      setMessage(`Measure ${selected.measure_number} saved for ${user.name}. Continue to practice review when ready.`)
      setSelectedId(null)
    } catch (saveError) {
      setError(saveError.message)
    } finally {
      setSaving(false)
    }
  }

  return <div className="measure-marker">
    <header className="mm-header"><a href="#/score-library">♫ SCORE COMPANION</a><span>● OFFLINE READY</span><MockUserControl /></header>
    <div className="mm-layout">
      <aside className="mm-sidebar"><nav aria-label="Score Companion"><a href="#/score-library">Score library</a><a href="#/practice-review">Practice review</a><a href="#/measure-marker" aria-current="page">Measure marker</a></nav></aside>
      <main className="mm-content">
        <h1>{count ? 'Select another measure' : 'Select a measure to mark'}</h1>
        <p className="mm-subtitle">{count ? 'Your saved measures remain marked for this demo user. Choose another measure, then mark it.' : 'Tap a measure, then choose Mark for practice.'}</p>
        {passages && <section className="mm-save-panel" aria-live="polite">
          <div><strong>{selected ? `Measure ${selected.measure_number} selected` : 'No measure selected'}</strong><span>{selected?.is_marked_for_practice ? 'This measure is already in practice review.' : 'Choose a measure, then save it to practice review.'}</span></div>
          <button className="mm-save" type="button" disabled={!selected || selected.is_marked_for_practice || saving} onClick={save}>{saving ? 'Saving…' : selected ? `Save measure ${selected.measure_number}` : 'Save selected measure'}</button>
        </section>}
        {passages && <><div className="mm-meta"><span>{user.name} | {score.movement} | Saved to practice review</span><strong>{count} marked {count === 1 ? 'measure' : 'measures'}</strong></div>
        <section className="mm-score" aria-labelledby="mm-score-title">
          <h2 id="mm-score-title">{score.movement.toUpperCase()} · {score.instrument.toUpperCase()}</h2>
          <div className="mm-grid">{passages.map((passage) => <button type="button" key={passage.id}
            className={`mm-measure${passage.id === selectedId ? ' is-selected' : ''}${passage.is_marked_for_practice ? ' is-saved' : ''}`}
            aria-pressed={passage.id === selectedId}
            aria-label={`Measure ${passage.measure_number}${passage.is_marked_for_practice ? ', saved for practice' : ''}`}
            onClick={() => { setSelectedId(passage.id); setMessage('') }}>
            <span>m. {passage.measure_number}</span><Staff />
            <span className="mm-badges">{passage.is_marked_for_practice && <b>✓ SAVED</b>}{passage.id === selectedId && <b>SELECTED</b>}</span>
          </button>)}</div>
        </section></>}
        {!passages && !error && <p className="mm-feedback" role="status">Loading your score…</p>}
        {error && <p className="mm-feedback" role="alert">{error}</p>}
        {passages && <><p className="mm-feedback" role="status">{message || (selected ? `Measure ${selected.measure_number} ${selected.is_marked_for_practice ? 'is already saved for practice.' : 'selected.'}` : 'Select a measure above.')}</p>
        {message && <a className="mm-review-link" href="#/practice-review">Open practice review →</a>}</>}
      </main>
    </div>
  </div>
}
