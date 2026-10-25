import assert from 'node:assert/strict'
import test from 'node:test'
import { initialPage, loadViewerData, pagePassages, samplePassages, sectionOptions } from './scoreViewerData.js'

test('empty library returns an explicitly identified sample at Section B, measure 24', async () => {
  const result = await loadViewerData(null, undefined, async () => ({ ok: true, json: async () => [] }))
  assert.equal(result.isSample, true)
  assert.equal(result.score.id, null)
  assert.equal(initialPage(result.passages, 4), 2)
  assert.deepEqual(pagePassages(result.passages, 2).map((item) => item.measure_number), [17, 18, 19, 20, 21, 22, 23, 24])
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
