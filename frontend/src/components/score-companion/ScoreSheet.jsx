import MeasurePreview from './MeasurePreview'

export default function ScoreSheet({ heading, passages, label = 'Score passages', notationLabel = 'Illustrative notation', emptyMessage = 'No measures have been added yet.', renderPassage = (passage) => <MeasurePreview passage={passage} /> }) {
  return (
    <section className="score-sheet" aria-label={label}>
      <div className="viewer-sheet-heading">
        <h2>{heading}</h2>
        {notationLabel && <span>{notationLabel}</span>}
      </div>
      {passages.length > 0 ? <div className="viewer-measure-grid">
        {passages.map((passage) => <div key={passage.id}>{renderPassage(passage)}</div>)}
      </div> : <p className="viewer-empty">{emptyMessage}</p>}
    </section>
  )
}
