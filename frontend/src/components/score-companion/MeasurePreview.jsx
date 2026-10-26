// Metadata preview only: this illustration is not a score-file/music renderer.
export default function MeasurePreview({ passage }) {
  return (
    <article className="viewer-measure" aria-label={'Section ' + passage.section + ', measure ' + passage.measure_number}>
      <span className="viewer-measure-label">m. {passage.measure_number}</span>
      <div className="viewer-staff" aria-hidden="true">
        <i /><i /><i /><i /><i />
        <b className="viewer-note note-one" /><b className="viewer-note note-two" />
        <b className="viewer-note note-three" /><b className="viewer-note note-four" />
      </div>
    </article>
  )
}
