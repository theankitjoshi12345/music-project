export default function PdfScoreReader({ score, passages, page, focusedPassageId, onPageChange, onSelect, onExtract, extracting, extractionError, onSave, savingId }) {
  const pageMeasures = passages.filter((passage) => passage.page_number === page)
  const complete = score.extraction_status === 'complete'
  const pdfUrl = `${score.source_file}#page=${page}&view=FitH`

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
      <iframe key={`${score.id}-${page}`} src={pdfUrl} title={`${score.title}, page ${page}`} />
    </div>
    <aside className="pdf-measures" aria-labelledby="detected-measures-title" aria-busy={Boolean(extracting)}>
      <h2 id="detected-measures-title">Measures</h2>
      {extracting ? <p role="status" className="pdf-extraction-status">Finding measures in your PDF… You can keep reading while this runs.</p>
        : complete ? <p role="status">{passages.length} measures detected. Review the numbering against your score.</p>
          : <><p>Find the measures in this PDF, then save the ones you want to practice.</p><button className="pdf-extract" type="button" onClick={onExtract}>{extractionError ? 'Retry extraction' : 'Extract measures'}</button></>}
      {extractionError && <p className="viewer-error" role="alert">{extractionError}</p>}
      {pageMeasures.length > 0 && <>
        <h3>Page {page} <span>· {pageMeasures.length} measures</span></h3>
        <ul className="pdf-measure-list">{pageMeasures.map((passage) => <li key={passage.id} className={passage.id === focusedPassageId ? 'is-focused' : ''}>
          <button type="button" className="pdf-measure-select" onClick={() => onSelect(passage)} aria-pressed={passage.id === focusedPassageId}>Measure {passage.measure_number}</button>
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
