import assert from 'node:assert/strict'
import { extractionCountdown, formatDuration } from './extractionTiming.js'
import test from 'node:test'
import { initialPage, loadViewerData, pagePassages, samplePassages, sectionOptions, scoreViewerHref } from './scoreViewerData.js'
import { requestExtraction } from './extractionRequest.js'

test('practice review links identify the exact score and passage', () => {
  const link = scoreViewerHref({ id: 70, score_id: 42 })
  assert.equal(link, '#/score-viewer?score=42&passage=70')
})

test('opening a saved passage selects its page before the default practice measure', () => {
  const passages = [
    { id: 7, section: 'B', measure_number: 24, page_number: 2 },
    { id: 70, section: 'C', measure_number: 40, page_number: 4 },
  ]
  assert.equal(initialPage(passages, 4, '70'), 4)
  assert.equal(initialPage(passages, 4, 'unknown'), 2)
})

test('empty library stays empty instead of inventing sample score data', async () => {
  const result = await loadViewerData(null, undefined, async () => ({ ok: true, json: async () => [] }))
  assert.deepEqual(result, { score: null, passages: [], isSample: false })
})

test('requested score loads details and passages without choosing another library entry', async () => {
  const calls = []
  const score = { id: 42, movement: 'Finale', instrument: 'Violin', page_count: 3 }
  const passages = [{ id: 7, section: 'C', measure_number: 60, page_number: 3 }]
  const signal = new AbortController().signal
  const result = await loadViewerData('42', signal, async (path, options) => {
    calls.push(path)
    assert.equal(options.signal, signal)
    return { ok: true, json: async () => path.endsWith('/passages/') ? passages : score }
  })
  assert.deepEqual(calls, ['/api/scores/42/', '/api/scores/42/passages/'])
  assert.deepEqual(result, { score, passages, isSample: false })
  assert.equal(initialPage(result.passages, 3), 3)
})

test('direct viewer entry resolves the first available library part', async () => {
  const calls = []
  await loadViewerData(null, undefined, async (path) => {
    calls.push(path)
    return { ok: true, json: async () => path === '/api/scores/' ? [{ id: 9 }] : [] }
  })
  assert.deepEqual(calls, ['/api/scores/', '/api/scores/9/', '/api/scores/9/passages/'])
})

test('HTTP failures remain errors instead of silently substituting sample data', async () => {
  await assert.rejects(loadViewerData('404', undefined, async () => ({ ok: false, status: 404 })), /could not be found/)
  await assert.rejects(loadViewerData(null, undefined, async () => { throw new Error('Network unavailable') }), /Network unavailable/)
})

test('invalid score links are rejected before making a request', async () => {
  await assert.rejects(loadViewerData('bad-id', undefined, async () => assert.fail('Unexpected request')), /numeric score ID/)
})

test('page navigation handles empty pages and derives the real sections', () => {
  assert.deepEqual(pagePassages([], 2), [])
  assert.equal(initialPage([], 4), 1)
  assert.deepEqual(sectionOptions(samplePassages), ['A', 'B', 'C'])
  assert.deepEqual(pagePassages(samplePassages, 4).map((item) => item.measure_number), [33, 34, 35, 36, 37, 38, 39, 40])
})

test('extraction deduplicates simultaneous requests and permits a retry after failure', async () => {
  let finish
  let calls = 0
  const request = () => { calls++; return new Promise((resolve) => { finish = resolve }) }
  const first = requestExtraction(123, {}, request)
  const second = requestExtraction(123, {}, request)
  assert.equal(calls, 1)
  finish({ ok: true, json: async () => ({ extraction_status: 'complete' }) })
  assert.deepEqual(await first, await second)
  await assert.rejects(requestExtraction(123, {}, async () => ({ ok: false, json: async () => ({ detail: 'Try again' }) })), /Try again/)
  const retried = await requestExtraction(123, {}, async () => ({ ok: true, json: async () => ({ extraction_status: 'complete' }) }))
  assert.equal(retried.extraction_status, 'complete')
})

test('conversion countdown uses the server start time across reloads and polling', () => {
  const started = Date.parse('2026-11-03T15:00:00Z')
  const score = { extraction_started_at: new Date(started).toISOString(), extraction_estimated_seconds: 315 }
  assert.deepEqual(extractionCountdown(score, started + 120000), { elapsed: 120, remaining: 195 })
  assert.deepEqual(extractionCountdown({ ...score }, started + 121000), { elapsed: 121, remaining: 194 })
  assert.equal(formatDuration(194), '03:14')
})

test('conversion overrun keeps elapsed time without negative or fake completed countdowns', () => {
  const started = Date.parse('2026-11-03T15:00:00Z')
  const score = { extraction_started_at: new Date(started).toISOString(), extraction_estimated_seconds: 30 }
  assert.deepEqual(extractionCountdown(score, started + 45000), { elapsed: 45, remaining: 0 })
  assert.equal(formatDuration(-10), '00:00')
})

test('conversion waits for server timing and tolerates a future server clock', () => {
  assert.equal(extractionCountdown({ extraction_started_at: null, extraction_estimated_seconds: 30 }), null)
  assert.equal(extractionCountdown({ extraction_started_at: 'invalid', extraction_estimated_seconds: 30 }), null)
  const future = Date.now() + 60000
  assert.deepEqual(extractionCountdown({ extraction_started_at: new Date(future).toISOString(), extraction_estimated_seconds: 45 }, future - 1000), { elapsed: 0, remaining: 45 })
})
