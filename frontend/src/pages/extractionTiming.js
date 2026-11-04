export function extractionCountdown(score, now = Date.now()) {
  const started = Date.parse(score.extraction_started_at)
  const estimate = score.extraction_estimated_seconds
  if (!Number.isFinite(started) || !Number.isFinite(estimate) || estimate <= 0) return null
  const elapsed = Math.max(0, Math.floor((now - started) / 1000))
  return { elapsed, remaining: Math.max(0, estimate - elapsed) }
}

export function formatDuration(seconds) {
  const total = Math.max(0, Math.floor(seconds))
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}
