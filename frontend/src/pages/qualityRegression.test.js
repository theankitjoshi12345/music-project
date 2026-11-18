import assert from 'node:assert/strict'
import test from 'node:test'

import { requestExtraction } from './extractionRequest.js'
import { pagePassages, scoreViewerHref } from './scoreViewerData.js'

test('extraction refuses malformed tickets and clears the in-flight request for a retry', async () => {
  let ticketCalls = 0
  const malformed = async () => {
    ticketCalls += 1
    return { ok: true, json: async () => ({ url: '/api/extract-without-token' }) }
  }

  await assert.rejects(requestExtraction('malformed-ticket', {}, malformed), /could not start/)

  const successful = async (path) => {
    ticketCalls += 1
    return path.includes('extraction-ticket')
      ? { ok: true, json: async () => ({ url: '/api/extract', token: 'retry-ticket' }) }
      : { ok: true, json: async () => ({ extraction_status: 'complete' }) }
  }
  assert.deepEqual(await requestExtraction('malformed-ticket', {}, successful), { extraction_status: 'complete' })
  assert.equal(ticketCalls, 3)
})

test('extraction accepts an already-running response and preserves per-score request isolation', async () => {
  const calls = []
  const request = async (path) => {
    calls.push(path)
    if (path.includes('extraction-ticket')) {
      const scoreId = path.split('/')[3]
      return { ok: true, json: async () => ({ url: `/api/extract/${scoreId}`, token: `ticket-${scoreId}` }) }
    }
    if (path.endsWith('/one')) return { ok: false, status: 409, json: async () => ({ detail: 'This score is already being extracted.' }) }
    return { ok: true, status: 200, json: async () => ({ extraction_status: 'complete', score: 'two' }) }
  }

  const [one, two] = await Promise.all([
    requestExtraction('one', {}, request),
    requestExtraction('two', {}, request),
  ])
  assert.match(one.detail, /already being extracted/)
  assert.deepEqual(two, { extraction_status: 'complete', score: 'two' })
  assert.equal(calls.filter(path => path.includes('extraction-ticket')).length, 2)
})

test('score links and page measures are stable when API data arrives out of order', () => {
  const passages = [
    { id: 3, section: 'B', measure_number: 2, page_number: 1 },
    { id: 2, section: 'A', measure_number: 2, page_number: 1 },
    { id: 1, section: 'A', measure_number: 1, page_number: 1 },
    { id: 4, section: 'C', measure_number: 1, page_number: 2 },
  ]
  assert.deepEqual(pagePassages(passages, 1).map(({ id }) => id), [1, 2, 3])
  assert.equal(scoreViewerHref({ id: 3, score_id: 44 }), '#/score-viewer?score=44&passage=3')
})
