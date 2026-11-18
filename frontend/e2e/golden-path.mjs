import assert from 'node:assert/strict'
import { chromium } from 'playwright'

const origin = process.env.E2E_ORIGIN
assert.ok(origin, 'Set E2E_ORIGIN to a running isolated Score Companion build.')

const musicXml = Buffer.from(`<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0"><part id="P1">
  <measure number="1"/><measure number="2"><print new-page="yes"/></measure>
</part></score-partwise>`)

const browser = await chromium.launch({ channel: process.env.E2E_BROWSER_CHANNEL || undefined, headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
const page = await context.newPage()
page.setDefaultTimeout(10_000)
let scoreId

try {
  const session = await context.request.get(`${origin}/api/session/`)
  assert.equal(session.status(), 200)
  assert.equal((await session.json()).auth_mode, 'demo', 'Golden-path CI uses its isolated demo test server.')

  await page.goto(`${origin}/#/score-library`)
  await page.getByLabel('Score file', { exact: true }).setInputFiles({
    name: 'p12-golden-path.musicxml', mimeType: 'application/vnd.recordare.musicxml+xml', buffer: musicXml,
  })
  const uploaded = page.waitForResponse(response => response.url().endsWith('/api/scores/upload/') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Add to library', exact: true }).click()
  const uploadResponse = await uploaded
  assert.equal(uploadResponse.status(), 201)
  scoreId = (await uploadResponse.json()).id

  await page.getByRole('button', { name: 'Save for practice', exact: true }).click()
  await page.getByRole('button', { name: 'Remove from practice', exact: true }).waitFor()

  await page.getByRole('navigation', { name: 'Main navigation', exact: true })
    .getByRole('link', { name: 'Practice review', exact: true }).click()
  const review = page.getByRole('article', { name: 'Practice measure 1', exact: true })
  await review.getByRole('button', { name: 'Mark practiced', exact: true }).click()
  await review.getByRole('button', { name: 'Practice again', exact: true }).waitFor()
  await review.getByRole('link', { name: 'Open measure', exact: false }).click()
  await page.getByRole('button', { name: 'Remove from practice', exact: true }).waitFor()

  console.log('PASS: P12 golden path uploads MusicXML, opens a measure, saves/reviews practice, and returns to the measure')
} finally {
  if (scoreId) {
    await context.request.delete(`${origin}/api/scores/${scoreId}/`, { headers: { 'X-Mock-User': 'alex' } }).catch(() => {})
  }
  await browser.close()
}
