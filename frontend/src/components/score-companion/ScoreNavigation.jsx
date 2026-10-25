export default function ScoreNavigation({ page, pageCount, onPageChange, sections = [], section = '', onSectionChange, context, measureRange }) {
  return (
    <section className="score-controls" aria-label="Score navigation">
      {context && <div className="score-context">{context}</div>}
      <div className="viewer-toolbar">
        <div className="navigation-row">
          <button type="button" onClick={() => onPageChange(page - 1)} disabled={page <= 1}>‹ Previous</button>
          <strong aria-live="polite">Page {page} of {pageCount}</strong>
          <button type="button" onClick={() => onPageChange(page + 1)} disabled={page >= pageCount}>Next ›</button>
        </div>
        {sections.length > 0 && onSectionChange && <label className="viewer-section-picker">Section
          <select aria-label="Jump to section" value={section} onChange={(event) => onSectionChange(event.target.value)}>
            {!section && <option value="">Choose section</option>}
            {sections.map((name) => <option key={name} value={name}>Section {name}</option>)}
          </select>
        </label>}
      </div>
      {measureRange && <p className="viewer-measure-range" aria-live="polite">{measureRange}</p>}
    </section>
  )
}
