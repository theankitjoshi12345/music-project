import { useEffect, useMemo, useRef, useState } from 'react'
import ExtractionProgress from './ExtractionProgress'
import LoadingSkeleton from '../components/score-companion/LoadingSkeleton'
import useMeasureKeyboard from './useMeasureKeyboard'
import { adjacentMeasure } from './measureNavigation'

export function ScoreImage({ src, alt }) {
  const [state, setState] = useState('loading')
  const [attempt, setAttempt] = useState(0)
  return <>
    {state === 'loading' && <LoadingSkeleton kind="notation" label="Loading score image…" />}
    {state === 'error' && <p className="viewer-error" role="alert">The score image did not load. <button type="button" onClick={() => { setState('loading'); setAttempt(current => current + 1) }}>Retry image</button></p>}
    <img key={attempt} src={src} alt={alt} onLoad={() => setState('ready')} onError={() => setState('error')} hidden={state !== 'ready'} />
  </>
}

export default function PdfScoreReader({ score, passages, page, focusedPassageId, onPageChange, onSelect, onExtract, extracting, extractionError, onSave, onRemove, savingId }) {
  const [view, setView] = useState('measure')
  const [jumpError, setJumpError] = useState('')
  const listRef = useRef(null)
  const ordered = useMemo(() => [...passages].sort((a, b) => a.page_number - b.page_number || a.measure_number - b.measure_number), [passages])
  const pageMeasures = ordered.filter(passage => passage.page_number === page)
  const selected = pageMeasures.find(passage => passage.id === focusedPassageId) ?? pageMeasures[0]
  const previous = adjacentMeasure(ordered, selected?.id, -1)
  const next = adjacentMeasure(ordered, selected?.id, 1)
  const complete = score.extraction_status === 'complete' && score.measure_layout_version >= 1

  function select(passage) {
    onSelect(passage)
    setView('measure')
    setJumpError('')
  }
  useMeasureKeyboard(ordered, selected?.id, select)
  useEffect(() => {
    const list = listRef.current
    const item = list?.querySelector(`[data-passage-id="${selected?.id}"]`)
    if (!item) return
    const itemBounds = item.getBoundingClientRect()
    const listBounds = list.getBoundingClientRect()
    if (itemBounds.top < listBounds.top) list.scrollBy({ top: itemBounds.top - listBounds.top, behavior: 'smooth' })
    else if (itemBounds.bottom > listBounds.bottom) list.scrollBy({ top: itemBounds.bottom - listBounds.bottom, behavior: 'smooth' })
  }, [selected?.id])

  function jump(event) {
    event.preventDefault()
    const number = Number(new FormData(event.currentTarget).get('measure'))
    const match = ordered.find(passage => passage.measure_number === number)
    if (match) select(match)
    else setJumpError('Choose a measure number shown in the list.')
  }

  return <section className={`pdf-reader${extracting ? ' is-extracting' : ''}`} aria-label="PDF score and detected measures">
    <div className="viewer-pdf">
      <div className="reader-viewbar">
        <div className="pdf-view-options" aria-label="Score view">
          <button type="button" aria-pressed={view === 'measure'} onClick={() => setView('measure')}>Selected measure</button>
          <button type="button" aria-pressed={view === 'page'} onClick={() => setView('page')}>Full page</button>
        </div>
        <a className="button-link" href={`${score.source_file}#page=${page}&view=FitH`} target="_blank" rel="noreferrer">Open original PDF ↗</a>
      </div>
      {view === 'measure' ? <section className="pdf-selected-measure" aria-label="Selected measure preview">
        <div className="reader-measure-heading"><h2>{selected ? `Measure ${selected.measure_number} · Page ${selected.page_number}` : 'Preparing your measures'}</h2>{selected?.is_marked_for_practice && <><span className="reader-saved">Saved for practice</span><a className="button-link" href="#/practice-review">Open practice list →</a></>}</div>
        {selected && <div className="reader-measure-actions">
          <div className="reader-step-controls" aria-label="Measure navigation">
            <button className="button-secondary" type="button" aria-label="Previous measure" disabled={!previous} onClick={() => select(previous)}>← Previous</button>
            <button className="button-secondary" type="button" aria-label="Next measure" disabled={!next} onClick={() => select(next)}>Next →</button>
          </div>
          <button className={selected.is_marked_for_practice ? 'button-secondary' : 'button-primary'} type="button" disabled={savingId !== null} onClick={() => selected.is_marked_for_practice ? onRemove(selected) : onSave(selected)} aria-label={`${selected.is_marked_for_practice ? 'Remove' : 'Save'} measure ${selected.measure_number} ${selected.is_marked_for_practice ? 'from' : 'for'} practice`}>
            {savingId === selected.id ? 'Saving…' : selected.is_marked_for_practice ? 'Remove from practice' : 'Save for practice'}
          </button>
        </div>}
        {selected && <p className="reader-keyboard-hint">Use ← and → arrow keys to move between measures.</p>}
        {selected?.preview_url ? <ScoreImage key={`${selected.id}:${JSON.stringify(selected.bounding_box)}`} src={selected.preview_url} alt={`Music notation for measure ${selected.measure_number}, page ${selected.page_number}`} />
          : <p className="reader-preparing">{extracting ? 'Finding measure positions. Choose Full page to read your score while this runs.' : 'Convert this PDF to open individual measures.'}</p>}
      </section> : <>
        <div className="reader-page-toolbar"><div className="pdf-page-controls" aria-label="PDF pages">
          <button type="button" aria-label="Previous PDF page" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>‹</button>
          <label>Page <select aria-label="PDF page" value={page} onChange={event => onPageChange(Number(event.target.value))}>{Array.from({ length: score.page_count }, (_, index) => <option key={index} value={index + 1}>{index + 1}</option>)}</select> of {score.page_count}</label>
          <button type="button" aria-label="Next PDF page" disabled={page >= score.page_count} onClick={() => onPageChange(page + 1)}>›</button>
        </div><p>Select a highlighted measure to open it.</p></div>
        <div className="pdf-page-image"><ScoreImage key={`${score.id}-${page}`} src={`/api/scores/${score.id}/pages/${page}/image/`} alt={`Full score page ${page}`} />
          <div className="pdf-measure-overlays">{pageMeasures.filter(passage => passage.bounding_box).map(passage => <button key={passage.id} type="button" aria-label={`View measure ${passage.measure_number} on score`} className={passage.id === selected?.id ? 'is-selected' : ''} style={{ left:`${passage.bounding_box.x * 100}%`, top:`${passage.bounding_box.y * 100}%`, width:`${passage.bounding_box.width * 100}%`, height:`${passage.bounding_box.height * 100}%` }} onClick={() => select(passage)} />)}</div>
        </div>
      </>}
    </div>
    <aside className="pdf-measures" aria-labelledby="detected-measures-title" aria-busy={Boolean(extracting)}>
      <h2 id="detected-measures-title">Measures</h2>
      {extracting ? <ExtractionProgress score={score} /> : complete ? <p role="status">{passages.length} measures ready. Select one to read it.</p> : <><p>Convert the PDF to find its measures.</p><button className="button-primary" type="button" onClick={onExtract}>{extractionError ? 'Retry conversion' : 'Find measures'}</button></>}
      {extractionError && <p className="viewer-error" role="alert">{extractionError}</p>}
      {ordered.length > 0 && <>
        <form className="reader-jump" onSubmit={jump}><label htmlFor="reader-measure-number">Go to measure</label><div><input id="reader-measure-number" name="measure" type="number" min="1" required placeholder="Number" /><button className="button-secondary" type="submit">Go</button></div></form>
        {jumpError && <p className="viewer-error" role="alert">{jumpError}</p>}
        <ul className="pdf-measure-list" ref={listRef}>{ordered.map((passage, index) => <li key={passage.id} data-passage-id={passage.id} className={passage.id === selected?.id ? 'is-focused' : ''}>
          {(index === 0 || ordered[index - 1].page_number !== passage.page_number) && <span className="reader-page-label">Page {passage.page_number}</span>}
          <button type="button" className="pdf-measure-select" onClick={() => select(passage)} aria-current={passage.id === selected?.id ? 'true' : undefined}>Measure {passage.measure_number}{passage.is_marked_for_practice && <span className="reader-list-saved" aria-label="Saved for practice">✓</span>}</button>
        </li>)}</ul>
      </>}
    </aside>
  </section>
}
