import { useEffect, useState } from 'react'
import { AppLayout, FeedbackPanel, MeasureJump, ScoreContext, ScoreNavigation, ScoreSheet, ScreenHeading } from '../components/score-companion'
import useScoreViewer from './useScoreViewer'
import { useMockSession } from '../mockSession'
import './ScoreViewer.css'

export default function ScoreViewer() {
  const { user } = useMockSession()
  const viewer = useScoreViewer(user)
  const [actionMessage, setActionMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const [savingId, setSavingId] = useState(null)
  const { score, visible, currentSections } = viewer
  const sourceIsPdf = score?.source_file?.toLowerCase().endsWith('.pdf')
  const pdfPageUrl = sourceIsPdf ? `${score.source_file}#page=${viewer.page}&view=FitH` : ''
  const context = score && <ScoreContext movement={score.movement} instrument={score.instrument} sections={currentSections} />
  const measureRange = visible.length ? 'Measures ' + visible[0].measure_number + '–' + visible.at(-1).measure_number : 'No measures on this page'

  useEffect(() => {
    if (!viewer.focusedPassageId) return
    document.getElementById(`measure-${viewer.focusedPassageId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [viewer.focusedPassageId, viewer.page])

  async function saveForPractice(passage) {
    setSavingId(passage.id); setActionError(''); setActionMessage('')
    try {
      await viewer.saveForPractice(passage)
      setActionMessage(`Measure ${passage.measure_number} is now in ${user.name}'s Practice Review.`)
    } catch (error) { setActionError(error.message) } finally { setSavingId(null) }
  }

  async function addPassage(event) {
    event.preventDefault(); setActionError(''); setActionMessage('')
    const form = event.currentTarget
    try {
      const passage = await viewer.addPassage({ section: form.section.value, measure_number: Number(form.measure_number.value), page_number: Number(form.page_number.value) })
      setActionMessage(`Measure ${passage.measure_number} was added. Use Mark for practice to send it to Practice Review.`)
      form.reset()
    } catch (error) { setActionError(error.message) }
  }

  return (
    <AppLayout className="score-viewer" status={viewer.isSample ? 'Sample score' : 'Score viewer'} activeHref="#/score-library" headingId="score-title" busy={viewer.loading}>
      <ScreenHeading
        id="score-title"
        byline="Score viewer & navigation · Ankit Joshi"
        title={score ? score.movement + ' — ' + score.instrument : 'Your score'}
        subtitle={score ? (score.title === score.movement ? 'Find your place. Pick up where rehearsal left off.' : score.title) : 'Open a part and find your place.'}
      />

      {viewer.loading && <FeedbackPanel>Loading your score…</FeedbackPanel>}
      {viewer.error && <FeedbackPanel title="We couldn’t open this score" tone="error" actions={<>
        <button type="button" onClick={viewer.retry}>Try again</button>
        <button type="button" onClick={viewer.showSample}>View sample score</button>
      </>}><p>{viewer.error}</p></FeedbackPanel>}

      {score && <>
        {viewer.isSample && <p className="viewer-sample">Sample score · No downloaded scores yet. This preview is not saved to your library.</p>}
        {!sourceIsPdf && <ScoreNavigation
          page={viewer.page}
          pageCount={score.page_count}
          onPageChange={viewer.changePage}
          sections={viewer.sections}
          section={currentSections[0] ?? ''}
          onSectionChange={viewer.changeSection}
          context={context}
          measureRange={sourceIsPdf ? undefined : measureRange}
        />}
        {sourceIsPdf ? <section className="viewer-pdf" aria-label={`Uploaded PDF page ${viewer.page}`}>
          <div className="viewer-pdf-heading"><div><a className="viewer-back" href="#/score-library">← Library</a><strong>{score.title}</strong><span>Your score is ready to read.</span></div><a href={score.source_file} target="_blank" rel="noreferrer">Open in new tab ↗</a></div>
          <iframe key={pdfPageUrl} src={score.source_file} title={`${score.title}`}>
            <a href={score.source_file}>Open the uploaded PDF.</a>
          </iframe>
        </section> : <>
        <ScoreSheet
          label={sourceIsPdf ? `Practice markers for PDF page ${viewer.page}` : 'Score page ' + viewer.page}
          heading={<ScoreContext movement={score.movement} instrument={score.instrument} sections={currentSections} separator=" / " />}
          passages={visible}
          focusedPassageId={viewer.focusedPassageId}
          renderPassage={(passage) => <div><div className="viewer-measure-card"><span className="viewer-measure-label">m. {passage.measure_number}</span><div className="viewer-staff" aria-hidden="true"><i /><i /><i /><i /><i /><b className="viewer-note note-one" /><b className="viewer-note note-two" /><b className="viewer-note note-three" /><b className="viewer-note note-four" /></div></div><button className="viewer-mark-button" type="button" disabled={viewer.isSample || passage.is_marked_for_practice || savingId === passage.id} onClick={() => saveForPractice(passage)}>{savingId === passage.id ? 'Saving…' : passage.is_marked_for_practice ? 'Saved to review ✓' : 'Mark for practice'}</button></div>}
          emptyMessage={sourceIsPdf ? 'No practice markers are on this page yet. Add a measure from the PDF below, then mark it for practice.' : 'No measures have been added for this page yet. Try another page or section.'}
        />
        {!viewer.isSample && score && <form className="viewer-add-measure" onSubmit={addPassage}><strong>Add a measure</strong><span>Enter the score position, then mark it for practice.</span><label>Section<input name="section" defaultValue="Start" required /></label><label>Measure<input name="measure_number" type="number" min="1" required /></label><label>Page<input name="page_number" type="number" min="1" max={score.page_count} defaultValue={viewer.page || 1} required /></label><button type="submit">Add measure</button></form>}
        {actionMessage && <p className="viewer-action-message" role="status">{actionMessage} <a href="#/practice-review">Open Practice Review →</a></p>}
        {actionError && <p className="viewer-error" role="alert">{actionError}</p>}
        </>}
        {!sourceIsPdf && <div className="viewer-bottom-row">
          <MeasureJump key={viewer.page} onJump={viewer.jumpToMeasure} />
          <p className="viewer-hint">Your place, at a glance. Use the page controls or jump to a section.</p>
        </div>}
      </>}
    </AppLayout>
  )
}
