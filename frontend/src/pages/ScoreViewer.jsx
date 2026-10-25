import { AppLayout, FeedbackPanel, MeasureJump, ScoreContext, ScoreNavigation, ScoreSheet, ScreenHeading } from '../components/score-companion'
import useScoreViewer from './useScoreViewer'
import './ScoreViewer.css'

export default function ScoreViewer() {
  const viewer = useScoreViewer()
  const { score, visible, currentSections } = viewer
  const context = score && <ScoreContext movement={score.movement} instrument={score.instrument} sections={currentSections} />
  const measureRange = visible.length ? 'Measures ' + visible[0].measure_number + '–' + visible.at(-1).measure_number : 'No measures on this page'

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
        <ScoreNavigation
          page={viewer.page}
          pageCount={score.page_count}
          onPageChange={viewer.changePage}
          sections={viewer.sections}
          section={currentSections[0] ?? ''}
          onSectionChange={viewer.changeSection}
          context={context}
          measureRange={measureRange}
        />
        <ScoreSheet
          label={'Score page ' + viewer.page}
          heading={<ScoreContext movement={score.movement} instrument={score.instrument} sections={currentSections} separator=" / " />}
          passages={visible}
          emptyMessage="No measures have been added for this page yet. Try another page or section."
        />
        <div className="viewer-bottom-row">
          <MeasureJump key={viewer.page} onJump={viewer.jumpToMeasure} />
          <p className="viewer-hint">Your place, at a glance. Use the page controls or jump to a section.</p>
        </div>
      </>}
    </AppLayout>
  )
}
