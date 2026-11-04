import { useEffect, useState } from 'react'
import { extractionCountdown, formatDuration } from './extractionTiming'

export default function ExtractionProgress({ score }) {
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [])
  const timing = extractionCountdown(score, now)
  const overdue = timing?.remaining === 0

  return <section className="pdf-extraction-progress" aria-label="PDF conversion progress">
    <p className="pdf-extraction-status" role="status"><span className="pdf-extraction-spinner" aria-hidden="true" />
      {overdue ? 'Taking longer than estimated' : 'Finding measures in your PDF…'}
    </p>
    {timing ? <>
      {!overdue && <div className="pdf-extraction-countdown">
        <span>Estimated time remaining</span>
        <time dateTime={`PT${timing.remaining}S`}>{formatDuration(timing.remaining)}</time>
      </div>}
      <p className="pdf-extraction-elapsed">Elapsed {formatDuration(timing.elapsed)} · {score.page_count} {score.page_count === 1 ? 'page' : 'pages'}</p>
    </> : <p>Starting conversion and checking your PDF…</p>}
    <p>{overdue ? 'Still working. Complex scores can take longer.' : 'This is an estimate. Score complexity and computer speed affect the time.'}</p>
    <p>You can view the full page while we prepare your measures.</p>
  </section>
}
