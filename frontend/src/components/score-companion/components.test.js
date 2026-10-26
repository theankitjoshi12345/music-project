import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

let server
let components
let App

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('../../../', import.meta.url)),
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
    appType: 'custom',
  })
  components = await server.ssrLoadModule('/src/components/score-companion/index.js')
  const appModule = await server.ssrLoadModule('/src/App.jsx')
  App = appModule.default
})

after(async () => { await server?.close() })

test('merged routing retains the library, viewer score links, and unimplemented screen placeholders', () => {
  const originalWindow = globalThis.window
  try {
    for (const [hash, expected] of [
      ['#/score-library', /Your offline score library/],
      ['#/score-viewer?score=42', /Score viewer &amp; navigation · Ankit Joshi/],
      ['#/measure-marker', /Matthew Pisani/],
      ['#/practice-review', /Jonathan Dempsey/],
    ]) {
      globalThis.window = { location: { hash } }
      assert.match(renderToStaticMarkup(h(App)), expected)
    }
  } finally {
    if (originalWindow === undefined) delete globalThis.window
    else globalThis.window = originalWindow
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
