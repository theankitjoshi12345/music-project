import { useState } from 'react'
import './MeasureMarker.css'

// Documented API-shaped demo passages; IDs are local demo IDs, not server IDs.
const initialPassages = Array.from({ length: 8 }, (_, i) => ({
  id: i + 17, section: 'B', measure_number: i + 17,
  page_number: 2, is_marked_for_practice: false,
}))
const storageKey = 'score-companion-measure-marker-demo-v1'
function loadPassages() {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '[]')
    return initialPassages.map(p => ({ ...p, is_marked_for_practice: Array.isArray(saved) && saved.includes(p.id) }))
  } catch { return initialPassages }
}
function Staff() {
  return <svg viewBox="0 0 220 70" aria-hidden="true">
    {[25, 35, 45, 55, 65].map(y => <line key={y} x1="0" x2="220" y1={y} y2={y} stroke="#91a5ba" />)}
    {[ [32,45], [67,55], [102,65], [137,45] ].map(([x,y]) => <g key={x}><ellipse cx={x} cy={y} rx="7" ry="5" fill="currentColor"/><line x1={x+6} x2={x+6} y1={y} y2={y-35} stroke="currentColor"/></g>)}
  </svg>
}
export default function MeasureMarker() {
  const [passages, setPassages] = useState(loadPassages)
  const [selectedId, setSelectedId] = useState(null)
  const [message, setMessage] = useState('')
  const selected = passages.find(p => p.id === selectedId)
  const count = passages.filter(p => p.is_marked_for_practice).length
  function save() {
    if (!selected || selected.is_marked_for_practice) return
    const next = passages.map(p => p.id === selectedId ? { ...p, is_marked_for_practice: true } : p)
    try {
      localStorage.setItem(storageKey, JSON.stringify(next.filter(p => p.is_marked_for_practice).map(p => p.id)))
      setPassages(next)
      setMessage(`Measure ${selected.measure_number} saved for practice. Choose another measure to continue.`)
      setSelectedId(null)
    } catch { setMessage('Could not save in this browser. Enable browser storage and try again.') }
  }
  return <div className="measure-marker">
    <header className="mm-header"><a href="#/score-library">♫ SCORE COMPANION</a><span>● OFFLINE READY</span></header>
    <div className="mm-layout">
      <aside className="mm-sidebar"><nav aria-label="Score Companion"><a href="#/score-library">Score library</a><a href="#/practice-review">Practice review</a><a href="#/measure-marker" aria-current="page">Measure marker</a></nav></aside>
      <main className="mm-content">
        <h1>{count ? 'Select another measure' : 'Select a measure to mark'}</h1>
        <p className="mm-subtitle">{count ? 'Your saved measures remain marked. Choose another measure, then mark it.' : 'Tap a measure, then choose Mark for practice.'}</p>
        <div className="mm-meta"><span>Demo score · Saved on this browser</span><strong>{count} marked {count === 1 ? 'measure' : 'measures'}</strong></div>
        <section className="mm-score" aria-labelledby="mm-score-title">
          <h2 id="mm-score-title">MOVEMENT I · PERCUSSION / SECTION B</h2>
          <div className="mm-grid">{passages.map(p => <button type="button" key={p.id}
            className={`mm-measure${p.id === selectedId ? ' is-selected' : ''}${p.is_marked_for_practice ? ' is-saved' : ''}`}
            aria-pressed={p.id === selectedId}
            aria-label={`Measure ${p.measure_number}${p.is_marked_for_practice ? ', saved for practice' : ''}`}
            onClick={() => { setSelectedId(p.id); setMessage('') }}>
            <span>m. {p.measure_number}</span><Staff/>
            <span className="mm-badges">{p.is_marked_for_practice && <b>✓ SAVED</b>}{p.id === selectedId && <b>SELECTED</b>}</span>
          </button>)}</div>
        </section>
        <p className="mm-feedback" role="status">{message || (selected ? `Measure ${selected.measure_number} ${selected.is_marked_for_practice ? 'is already saved for practice.' : 'selected.'}` : 'Select a measure above.')}</p>
        <button className="mm-save" type="button" disabled={!selected || selected.is_marked_for_practice} onClick={save}>Mark {selected ? `measure ${selected.measure_number} ` : ''}for practice →</button>
      </main>
    </div>
  </div>
}
