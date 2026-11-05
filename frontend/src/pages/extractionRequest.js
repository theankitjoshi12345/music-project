// Share an in-flight request across remounts/tabs within this app instance.
const pending = new Map()

export function requestExtraction(scoreId, headers = {}, request = fetch) {
  if (pending.has(scoreId)) return pending.get(scoreId)
  const task = (async () => {
    const response = await request(`/api/scores/${scoreId}/extract-measures/`, { method: 'POST', headers })
    const data = await response.json().catch(() => ({}))
    const alreadyRunning = response.status === 409 && data.detail?.includes('already being extracted')
    if (!response.ok && !alreadyRunning) {
      throw new Error(data.detail || 'Measure extraction failed. Please retry.')
    }
    return data
  })().finally(() => pending.delete(scoreId))
  pending.set(scoreId, task)
  return task
}
