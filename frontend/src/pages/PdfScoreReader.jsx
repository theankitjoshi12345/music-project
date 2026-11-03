import { useState } from 'react'

function ScoreImage({ src, alt }) {
  const [state, setState] = useState('loading')
  const [attempt, setAttempt] = useState(0)
  return <>
    {state === 'loading' && <p className="pdf-image-status" role="status">Loading score image…</p>}
    {state === 'error' && <p className="viewer-error" role="alert">The score image did not load. <button type="button" onClick={() => { setState('loading'); setAttempt((current) => current + 1) }}>Retry image</button></p>}
    <img key={attempt} src={src} alt={alt} onLoad={() => setState('ready')} onError={() => setState('error')} hidden={state === 'error'} />
  </>
}

export default function PdfScoreReader({ score, passages, page, focusedPassageId, onPageChange, onSelect, onExtract, extracting, extractionError, onSave, savingId }) {
  const [view, setView] = useState('measure')
  const pageMeasures = passages.filter((passage) => passage.page_number === page)
  const selected = passages.find((passage) => passage.id === focusedPassageId) ?? pageMeasures[0]
  const complete = score.extraction_status === 'complete'
  const previewsReady = score.measure_layout_version >= 1
  const pdfUrl = `${score.source_file}#page=${page}&view=FitH`

  function select(passage) {
    onSelect(passage)
    setView('measure')
  }

  return <section className="pdf-reader" aria-label="PDF score and detected measures">
    <div className="viewer-pdf">
      <div className="viewer-pdf-heading">
        <a className="viewer-back" href="#/score-library">← Library</a>
        <div className="pdf-page-controls" aria-label="PDF pages">
          <button type="button" disabled={page <= 1} onClick={() => onPageChange(page - 1)} aria-label="Previous PDF page">‹</button>
          <label>Page <select aria-label="PDF page" value={page} onChange={(event) => onPageChange(Number(event.target.value))}>
            {Array.from({ length: score.page_count }, (_, index) => <option key={index} value={index + 1}>{index + 1}</option>)}
          </select> of {score.page_count}</label>
          <button type="button" disabled={page >= score.page_count} onClick={() => onPageChange(page + 1)} aria-label="Next PDF page">›</button>
        </div>
        <a href={pdfUrl} target="_blank" rel="noreferrer">Open PDF ↗</a>
      </div>
      <div className="pdf-view-options" aria-label="Score view">
        <button type="button" aria-current={view === 'measure' ? 'true' : undefined} onClick={() => setView('measure')}>Selected measure</button>
        <button type="button" aria-current={view === 'page' ? 'true' : undefined} onClick={() => setView('page')}>Full page</button>
      </div>
      {view === 'measure' ? <section className="pdf-selected-measure" aria-label="Selected measure preview">
        <h2>{selected ? `Measure ${selected.measure_number} · Page ${selected.page_number}` : 'Select a measure'}</h2>
        {selected?.preview_url ? <ScoreImage key={`${selected.id}:${JSON.stringify(selected.bounding_box)}`} src={selected.preview_url} alt={`Music notation for measure ${selected.measure_number}, page ${selected.page_number}`} />
          : <p>{extracting ? 'Preparing measure images from your PDF…' : 'Extract measure previews to see the music here.'}</p>}
      </section> : <div className="pdf-page-image">
        <ScoreImage key={`${score.id}-${page}`} src={`/api/scores/${score.id}/pages/${page}/image/`} alt={`Full score page ${page}`} />
        <div className="pdf-measure-overlays">{pageMeasures.filter((passage) => passage.bounding_box).map((passage) => <button
          key={passage.id} type="button" aria-label={`View measure ${passage.measure_number} on score`}
          className={passage.id === selected?.id ? 'is-selected' : ''}
          style={{ left: `${passage.bounding_box.x * 100}%`, top: `${passage.bounding_box.y * 100}%`, width: `${passage.bounding_box.width * 100}%`, height: `${passage.bounding_box.height * 100}%` }}
          onClick={() => select(passage)} />)}</div>
      </div>}
    </div>
    <aside className="pdf-measures" aria-labelledby="detected-measures-title" aria-busy={Boolean(extracting)}>
      <h2 id="detected-measures-title">Measures</h2>
      {extracting ? <p role="status" className="pdf-extraction-status">Finding measures in your PDF… You can keep reading while this runs.</p>
        : complete && previewsReady ? <p role="status">{passages.length} measures detected. Select one to see its music.</p>
          : <><p>Find the measures in this PDF, then save the ones you want to practice.</p><button className="pdf-extract" type="button" onClick={onExtract}>{extractionError ? 'Retry extraction' : complete ? 'Prepare measure previews' : 'Extract measures'}</button></>}
      {extractionError && <p className="viewer-error" role="alert">{extractionError}</p>}
      {pageMeasures.length > 0 && <>
        <h3>Page {page} <span>· {pageMeasures.length} measures</span></h3>
        <ul className="pdf-measure-list">{pageMeasures.map((passage) => <li id={`measure-${passage.id}`} key={passage.id} className={passage.id === focusedPassageId ? 'is-focused' : ''}>
          <button type="button" className="pdf-measure-select" onClick={() => select(passage)} aria-current={passage.id === focusedPassageId ? 'true' : undefined}>Measure {passage.measure_number}</button>
          <button type="button" className="pdf-measure-save" disabled={passage.is_marked_for_practice || savingId !== null} onClick={() => onSave(passage)} aria-label={passage.is_marked_for_practice ? `Measure ${passage.measure_number} saved to practice` : `Save measure ${passage.measure_number} for practice`}>
            {savingId === passage.id ? 'Saving…' : passage.is_marked_for_practice ? 'Saved ✓' : '+ Practice'}
          </button>
        </li>)}</ul>
      </>}
      {complete && pageMeasures.length === 0 && <p>No measures were detected on this page.</p>}
      <a className="pdf-review-link" href="#/practice-review">Practice review →</a>
    </aside>
  </section>
}
