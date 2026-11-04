import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

let server
let components
let App
let PdfScoreReader
let ExtractionProgress

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('../../../', import.meta.url)),
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
    appType: 'custom',
  })
  components = await server.ssrLoadModule('/src/components/score-companion/index.js')
  const appModule = await server.ssrLoadModule('/src/App.jsx')
  App = appModule.default
  PdfScoreReader = (await server.ssrLoadModule('/src/pages/PdfScoreReader.jsx')).default
  ExtractionProgress = (await server.ssrLoadModule('/src/pages/ExtractionProgress.jsx')).default
})

after(async () => { await server?.close() })

test('integrated routing renders all four screens and preserves viewer score links', () => {
  const originalWindow = globalThis.window
  const originalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage')
  try {
    Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: { getItem: () => null } })
    for (const [hash, expected] of [
      ['#/score-library', /Open a score\. Stay in the music\./],
      ['#/score-viewer?score=42', /Score viewer &amp; navigation · Ankit Joshi/],
      ['#/measure-marker', /Select a measure to mark/],
      ['#/practice-review', /<h1>Practice review<\/h1>/],
    ]) {
      globalThis.window = { location: { hash } }
      assert.match(renderToStaticMarkup(h(App)), expected)
    }
  } finally {
    if (originalWindow === undefined) delete globalThis.window
    else globalThis.window = originalWindow
    if (originalStorage) Object.defineProperty(globalThis, 'localStorage', originalStorage)
    else delete globalThis.localStorage
  }
})

test('shared layout supports another screen with its own active navigation and content', () => {
  const html = renderToStaticMarkup(h(components.AppLayout, {
    activeHref: '#/practice-review', status: 'Practice review', headingId: 'review-title',
  }, h(components.ScreenHeading, { id: 'review-title', title: 'Saved passages' })))
  assert.match(html, /href="#\/practice-review" aria-current="page"/)
  assert.doesNotMatch(html, /href="#\/score-library" aria-current/)
  assert.match(html, /aria-labelledby="review-title"/)
  assert.match(html, /<h1 id="review-title">Saved passages<\/h1>/)
  assert.doesNotMatch(html, /Ankit|Movement I/)
})

test('page controls disable previous and next at their respective boundaries', () => {
  const first = renderToStaticMarkup(h(components.ScoreNavigation, { page: 1, pageCount: 4, onPageChange() {} }))
  const last = renderToStaticMarkup(h(components.ScoreNavigation, { page: 4, pageCount: 4, onPageChange() {} }))
  assert.match(first, /disabled="">‹ Previous/)
  assert.doesNotMatch(first, /disabled="">Next/)
  assert.match(last, /disabled="">Next/)
  assert.doesNotMatch(last, /disabled="">‹ Previous/)
})

test('sheet renderer can be composed with another owners controls', () => {
  const passage = { id: 24, section: 'B', measure_number: 24 }
  const html = renderToStaticMarkup(h(components.ScoreSheet, {
    passages: [passage], heading: 'Section B',
    renderPassage: (item) => h('div', null,
      h(components.MeasurePreview, { passage: item }),
      h('button', { type: 'button' }, 'Select measure ' + item.measure_number)),
  }))
  assert.match(html, /Illustrative notation/)
  assert.match(html, /Section B, measure 24/)
  assert.match(html, /Select measure 24/)
})

test('empty sheets and request failures expose useful messages', () => {
  const empty = renderToStaticMarkup(h(components.ScoreSheet, { passages: [], heading: 'Saved passages', emptyMessage: 'Nothing saved yet.' }))
  assert.match(empty, /Nothing saved yet/)
  const error = renderToStaticMarkup(h(components.FeedbackPanel, { tone: 'error', title: 'Could not load parts', actions: h('button', null, 'Retry') }, 'Check the connection.'))
  assert.match(error, /role="alert"/)
  assert.match(error, /Could not load parts/)
  assert.match(error, /Retry/)
})

test('multiple measure-jump forms keep distinct accessible label associations', () => {
  const html = renderToStaticMarkup(h('div', null,
    h(components.MeasureJump, { onJump() {} }),
    h(components.MeasureJump, { onJump() {} })))
  const labels = [...html.matchAll(/for="([^"]+)"/g)].map((match) => match[1])
  const inputs = [...html.matchAll(/<input[^>]*?\sid="([^"]+)"/g)].map((match) => match[1])
  assert.equal(labels.length, 2)
  assert.notEqual(labels[0], labels[1])
  assert.deepEqual(inputs, labels)
})

test('PDF reader exposes actual detected measures, saved state, and the correct PDF page', () => {
  const html = renderToStaticMarkup(h(PdfScoreReader, {
    score: { id: 6, title: 'Uploaded part', source_file: '/media/part.pdf', page_count: 2, extraction_status: 'complete', measure_layout_version: 1 },
    passages: [{ id: 40, measure_number: 29, page_number: 1 }, { id: 41, measure_number: 30, page_number: 2, is_marked_for_practice: true, preview_url: '/api/passages/41/preview/' }],
    page: 2, savingId: null, onPageChange() {}, onSelect() {}, onSave() {},
  }))
  assert.match(html, /href="\/media\/part.pdf#page=2&amp;view=FitH"/)
  assert.match(html, /src="\/api\/passages\/41\/preview\/"/)
  assert.match(html, /Music notation for measure 30, page 2/)
  assert.match(html, /2 measures detected/)
  assert.match(html, /Measure 30 saved to practice/)
  assert.doesNotMatch(html, /Measure 29|Illustrative notation|Extract measures/)
})

test('PDF reader provides progress and retry instead of an unexplained empty score', () => {
  const props = { score: { title: 'Part', source_file: '/media/part.pdf', page_count: 1 }, passages: [], page: 1, onPageChange() {}, onExtract() {} }
  const processing = renderToStaticMarkup(h(PdfScoreReader, { ...props, extracting: true }))
  assert.match(processing, /Finding measures in your PDF/)
  const failed = renderToStaticMarkup(h(PdfScoreReader, { ...props, extractionError: 'Recognition unavailable' }))
  assert.match(failed, /Retry extraction/)
  assert.match(failed, /role="alert">Recognition unavailable/)
})

test('PDF conversion shows an explicitly estimated countdown and elapsed time', () => {
  const html = renderToStaticMarkup(h(ExtractionProgress, { score: {
    page_count: 2, extraction_started_at: new Date(Date.now() + 1000).toISOString(), extraction_estimated_seconds: 315,
  } }))
  assert.match(html, /Estimated time remaining/)
  assert.match(html, /05:15/)
  assert.match(html, /Elapsed 00:00 · 2 pages/)
  assert.match(html, /This is an estimate/)
})

test('PDF conversion overrun still shows work in progress rather than a completed timer', () => {
  const html = renderToStaticMarkup(h(ExtractionProgress, { score: {
    page_count: 2, extraction_started_at: new Date(Date.now() - 60000).toISOString(), extraction_estimated_seconds: 30,
  } }))
  assert.match(html, /Taking longer than estimated/)
  assert.match(html, /Still working/)
  assert.doesNotMatch(html, /<time|Estimated time remaining/)
})
