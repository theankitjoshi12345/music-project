// Share an in-flight request across remounts/tabs within this app instance.
const pending = new Map()

export function requestExtraction(scoreId, headers = {}, request = fetch) {
  if (pending.has(scoreId)) return pending.get(scoreId)
  const task = (async () => {
    const response = await request(`/api/scores/${scoreId}/extract-measures/`, { method: 'POST', headers })
    const data = await response.json().catch(() => ({}))
    if (!response.ok && response.status !== 409) {
      throw new Error(data.detail || 'Measure extraction failed. Please retry.')
    }
    return data
  })().finally(() => pending.delete(scoreId))
  pending.set(scoreId, task)
  return task
}
