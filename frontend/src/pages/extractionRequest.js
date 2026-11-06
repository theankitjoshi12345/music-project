// Share an in-flight request across remounts/tabs within this app instance.
const pending = new Map()

export function requestExtraction(scoreId, headers = {}, request = fetch) {
  if (pending.has(scoreId)) return pending.get(scoreId)
  const task = (async () => {
    const ticketResponse = await request(`/api/scores/${scoreId}/extraction-ticket/`, { method: 'POST', headers })
    const ticket = await ticketResponse.json().catch(() => ({}))
    if (!ticketResponse.ok || !ticket.url || !ticket.token) {
      throw new Error(ticket.detail || 'Measure extraction could not start. Please retry.')
    }
    const response = await request(ticket.url, {
      method: 'POST', headers: { Authorization: `Bearer ${ticket.token}` },
    })
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
