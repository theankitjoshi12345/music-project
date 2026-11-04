import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { chromium } from 'playwright'

// This test creates and deletes only its own fixture, against an empty test library.
const origin = process.env.E2E_ORIGIN
const pdf = process.env.E2E_PDF
assert.ok(origin && pdf, 'Set E2E_ORIGIN to an isolated app and E2E_PDF to a sheet-music PDF.')
const output = path.resolve(process.env.E2E_OUTPUT || '../tmp/e2e')
fs.mkdirSync(output, { recursive: true })
const browser = await chromium.launch({ channel: process.env.E2E_BROWSER_CHANNEL || undefined, headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
const page = await context.newPage()
const errors = []
page.on('pageerror', error => errors.push(error.message))
let score
const api = async (route, user = 'alex', options = {}) => context.request.fetch(`${origin}/api/${route}`, { ...options, headers: { 'X-Mock-User': user, ...options.headers } })
const json = async (route, user = 'alex') => {
  const response = await api(route, user)
  assert.equal(response.status(), 200, route)
  return response.json()
}
const nav = () => page.getByRole('navigation', { name: 'Main navigation', exact: true })
async function notation(passage) {
  await page.getByRole('heading', { name: `Measure ${passage.measure_number} · Page ${passage.page_number}`, exact: true }).waitFor()
  await page.waitForFunction(({ number, pageNumber }) => {
    const image = document.querySelector(`img[alt="Music notation for measure ${number}, page ${pageNumber}"]`)
    return image?.complete && image.naturalWidth > 20
  }, { number: passage.measure_number, pageNumber: passage.page_number })
}
async function jump(passage) {
  await page.getByLabel('Go to measure', { exact: true }).fill(String(passage.measure_number))
  await page.getByRole('button', { name: 'Go', exact: true }).click()
  await notation(passage)
}
async function noOverflow() {
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'Page must fit the viewport')
}

async function appearanceCheck(target) {
  const palettes = [['violet', 'Violet Jam'], ['peach', 'Peach Pop'], ['mint', 'Mint Groove']]
  for (const [id, name] of palettes) {
    await page.locator('.theme-picker summary').click()
    await page.getByRole('button', { name, exact: false }).click()
    assert.equal(await page.locator('.score-companion').getAttribute('data-color-theme'), id)
    const contrast = await page.evaluate(() => {
      const root = document.querySelector('.score-companion')
      const probe = document.createElement('span')
      probe.hidden = true
      root.append(probe)
      function luminance(rgb) {
        const values = rgb.match(/[\d.]+/g).slice(0, 3).map(Number).map(value => {
          const n = value / 255
          return n <= .04045 ? n / 12.92 : ((n + .055) / 1.055) ** 2.4
        })
        return .2126 * values[0] + .7152 * values[1] + .0722 * values[2]
      }
      const pairs = [['--accent', 'white'], ['--accent', '--soft'], ['--muted', '--background'], ['--muted', '--soft'], ['--ink', '--art-primary'], ['--ink', '--art-secondary'], ['--success', '--success-soft'], ['--danger', 'white']]
      const result = pairs.map(([text, background]) => {
        probe.style.color = `var(${text})`
        probe.style.backgroundColor = background.startsWith('--') ? `var(${background})` : background
        const style = getComputedStyle(probe)
        const a = luminance(style.color), b = luminance(style.backgroundColor)
        return { pair: `${text}/${background}`, ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05) }
      })
      probe.remove()
      return result
    })
    for (const pair of contrast) assert.ok(pair.ratio >= 4.5, `${name}: ${pair.pair} contrast ${pair.ratio.toFixed(2)}`)
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: width < 768 ? 844 : 1000 })
      await noOverflow()
      await page.locator('.theme-picker summary').click()
      await noOverflow()
      await page.keyboard.press('Escape')
      assert.equal(await page.locator('.theme-picker').getAttribute('open'), null)
      await page.getByRole('link', { name: 'Open measure', exact: false }).click()
      await notation(target)
      await noOverflow()
      assert.equal(await page.locator('.score-companion').getAttribute('data-color-theme'), id)
      assert.equal(await page.locator('.pdf-selected-measure').evaluate(el => getComputedStyle(el).backgroundColor), 'rgb(255, 255, 255)')
      if (width === 390 || width === 1440) await page.screenshot({ path: path.join(output, `${id}-reader-${width}.png`), fullPage: true })
      await nav().getByRole('link', { name: 'Library', exact: true }).click()
      await page.getByRole('link', { name: 'Open score', exact: false }).waitFor()
      await noOverflow()
      if (width === 390 || width === 1440) await page.screenshot({ path: path.join(output, `${id}-library-${width}.png`), fullPage: true })
      await nav().getByRole('link', { name: 'Practice review', exact: true }).click()
      await page.getByRole('article', { name: `Practice measure ${target.measure_number}`, exact: true }).waitFor()
    }
    await page.reload()
    await page.getByRole('article', { name: `Practice measure ${target.measure_number}`, exact: true }).waitFor()
    assert.equal(await page.locator('.score-companion').getAttribute('data-color-theme'), id)
    console.log(`PASS: ${name} contrast, 320/390/768/1440 layouts, white notation and persistence`)
  }
  await page.locator('.theme-picker summary').click()
  await page.getByRole('button', { name: 'Violet Jam', exact: false }).click()
}
const delayRead = async route => {
  if (route.request().method() === 'GET') await new Promise(resolve => setTimeout(resolve, 350))
  await route.continue().catch(() => {})
}

try {
  assert.deepEqual(await json('scores/'), [], 'Use an empty, isolated database/media directory.')
  await page.route(/\/api\/scores\/$/, delayRead)
  await page.route(/\/api\/scores\/\d+\/(?:passages\/)?$/, delayRead)
  await page.route(/\/api\/passages\/\d+\/preview\//, delayRead)
  await page.goto(`${origin}/#/score-library`)
  await page.getByRole('status').filter({ hasText: 'Loading your score library' }).waitFor()
  await page.getByRole('heading', { name: 'No scores yet', exact: true }).waitFor()
  await page.getByLabel('Score file', { exact: true }).setInputFiles({ name: 'Laverre City.pdf', mimeType: 'application/pdf', buffer: fs.readFileSync(pdf) })
  const uploaded = page.waitForResponse(response => response.url().endsWith('/api/scores/upload/') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Add to library', exact: true }).click()
  const uploadedResponse = await uploaded
  assert.equal(uploadedResponse.status(), 201)
  score = await uploadedResponse.json()
  const progress = page.getByRole('region', { name: 'PDF conversion progress', exact: true })
  await progress.locator('time').waitFor()
  const firstTime = await progress.locator('time').innerText()
  await page.waitForFunction(first => document.querySelector('.pdf-extraction-countdown time')?.textContent !== first, firstTime)
  const started = (await json(`scores/${score.id}/`)).extraction_started_at
  await page.reload()
  await progress.locator('time').waitFor()
  assert.equal((await json(`scores/${score.id}/`)).extraction_started_at, started)
  await page.screenshot({ path: path.join(output, 'conversion-countdown.png'), fullPage: true })
  await page.getByRole('button', { name: 'Full page', exact: true }).click()
  await page.getByAltText('Full score page 1', { exact: true }).waitFor({ state: 'visible' })
  await progress.waitFor({ state: 'detached', timeout: 720000 })
  const completed = await json(`scores/${score.id}/`)
  assert.equal(completed.extraction_status, 'complete')
  const passages = await json(`scores/${score.id}/passages/`)
  assert.ok(passages.length >= 3)
  if (process.env.E2E_EXPECTED_MEASURES) assert.equal(passages.length, Number(process.env.E2E_EXPECTED_MEASURES))
  const first = passages[0]
  const second = passages[1]
  const target = passages.find(passage => passage.page_number > first.page_number) || passages[2]
  await page.getByRole('button', { name: `View measure ${first.measure_number} on score`, exact: true }).click()
  await notation(first)
  assert.equal(await progress.count(), 0)
  console.log('PASS: real PDF upload, ticking countdown, refresh continuity, completion and notation')

  await page.keyboard.press('ArrowRight')
  await page.getByRole('status').filter({ hasText: 'Loading score image' }).waitFor()
  await notation(second)
  await page.keyboard.press('ArrowLeft'); await notation(first)
  await page.keyboard.press('ArrowLeft'); await notation(first)
  await page.getByLabel('Go to measure', { exact: true }).fill(String(target.measure_number))
  await page.keyboard.press('ArrowRight')
  await notation(first)
  await page.getByRole('button', { name: 'Go', exact: true }).click()
  await notation(target)
  const targetIndex = passages.findIndex(passage => passage.id === target.id)
  const scrollBefore = await page.evaluate(() => window.scrollY)
  await page.keyboard.press('ArrowLeft'); await notation(passages[targetIndex - 1])
  assert.ok(Math.abs(await page.evaluate(() => window.scrollY) - scrollBefore) < 4, 'Keyboard navigation should keep the reader in view')
  await page.getByRole('button', { name: 'Next measure', exact: true }).click(); await notation(target)
  await jump(passages.at(-1))
  assert.ok(await page.getByRole('button', { name: 'Next measure', exact: true }).isDisabled())
  await jump(target)
  console.log('PASS: arrow keys, page-boundary navigation, first/last boundaries and typing protection')

  const imageTarget = passages[2]
  const imagePattern = new RegExp(`/api/passages/${imageTarget.id}/preview/`)
  const failImage = route => route.fulfill({ status: 500, body: 'Test image failure' })
  await page.route(imagePattern, failImage)
  await page.getByLabel('Go to measure', { exact: true }).fill(String(imageTarget.measure_number))
  await page.getByRole('button', { name: 'Go', exact: true }).click()
  await page.getByRole('button', { name: 'Retry image', exact: true }).waitFor()
  await page.unroute(imagePattern, failImage)
  await page.getByRole('button', { name: 'Retry image', exact: true }).click()
  await notation(imageTarget)
  await jump(target)

  await page.getByRole('button', { name: `Save measure ${target.measure_number} for practice`, exact: true }).click()
  await page.getByRole('button', { name: `Remove measure ${target.measure_number} from practice`, exact: true }).waitFor()
  let mark = (await json('practice-marks/'))[0]
  await api(`practice-marks/${mark.id}/`, 'alex', { method: 'PATCH', data: { note: 'Disposable note to delete' } })
  await page.route('**/api/practice-marks/', delayRead)
  await nav().getByRole('link', { name: 'Practice review', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Loading practice review' }).waitFor()
  let card = page.getByRole('article', { name: `Practice measure ${target.measure_number}`, exact: true })
  await card.getByRole('button', { name: 'Mark practiced', exact: true }).click()
  await card.getByRole('button', { name: 'Practice again', exact: true }).waitFor()
  await appearanceCheck(target)
  await page.screenshot({ path: path.join(output, 'review-1440.png'), fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 }); await noOverflow()
  await page.screenshot({ path: path.join(output, 'review-390.png'), fullPage: true })
  await page.setViewportSize({ width: 1440, height: 1000 })
  await card.getByRole('link', { name: 'Open measure', exact: false }).click()
  await notation(target)

  // A failed deletion must retain the item on both client and server.
  const failDelete = route => route.request().method() === 'DELETE' ? route.fulfill({ status: 500, json: { detail: 'Test failure' } }) : route.continue()
  await page.route(`**/api/practice-marks/${mark.id}/`, failDelete)
  await page.getByRole('button', { name: `Remove measure ${target.measure_number} from practice`, exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'could not be removed' }).waitFor()
  assert.equal((await json('practice-marks/')).length, 1)
  await page.unroute(`**/api/practice-marks/${mark.id}/`, failDelete)
  await page.getByRole('button', { name: `Remove measure ${target.measure_number} from practice`, exact: true }).click()
  await page.getByRole('button', { name: `Save measure ${target.measure_number} for practice`, exact: true }).waitFor()
  assert.deepEqual(await json('practice-marks/'), [])
  await page.reload(); await notation(target)
  await page.getByRole('button', { name: `Save measure ${target.measure_number} for practice`, exact: true }).click()
  await page.getByRole('button', { name: `Remove measure ${target.measure_number} from practice`, exact: true }).waitFor()
  const newMark = (await json('practice-marks/'))[0]
  assert.notEqual(newMark.id, mark.id)
  assert.equal(newMark.note, '')
  const samResponse = await api('practice-marks/', 'sam', { method: 'POST', data: { passage_id: target.id, note: 'Sam keeps this' } })
  assert.equal(samResponse.status(), 201)
  await nav().getByRole('link', { name: 'Practice review', exact: true }).click()
  card = page.getByRole('article', { name: `Practice measure ${target.measure_number}`, exact: true })
  await card.getByRole('button', { name: 'Remove from practice', exact: true }).click()
  await page.getByRole('heading', { name: 'No saved practice measures yet', exact: true }).waitFor()
  assert.deepEqual(await json('practice-marks/'), [])
  assert.equal((await json('practice-marks/', 'sam')).length, 1)
  await page.getByLabel('Practice profile', { exact: true }).selectOption('sam')
  await page.getByText('Sam keeps this', { exact: true }).waitFor()
  await page.getByRole('button', { name: 'Remove from practice', exact: true }).click()
  await page.getByRole('heading', { name: 'No saved practice measures yet', exact: true }).waitFor()
  await page.getByLabel('Practice profile', { exact: true }).selectOption('alex')
  console.log('PASS: practice save/resolve/open, failed removal recovery, permanent note deletion and user isolation')

  await nav().getByRole('link', { name: 'Library', exact: true }).click()
  await page.getByText('Score options', { exact: true }).click()
  await page.getByRole('link', { name: 'Practice marker', exact: false }).click()
  await page.getByRole('button', { name: 'Next measure', exact: true }).waitFor()
  await page.keyboard.press('ArrowRight'); await notation(second)
  await page.getByRole('button', { name: 'Save for practice', exact: true }).click()
  await page.getByRole('button', { name: 'Remove from practice', exact: true }).click()
  await page.getByRole('button', { name: 'Save for practice', exact: true }).waitFor()
  assert.deepEqual(await json('practice-marks/'), [])
  await page.screenshot({ path: path.join(output, 'marker-1440.png'), fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 }); await noOverflow()
  await page.screenshot({ path: path.join(output, 'marker-390.png'), fullPage: true })
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.getByRole('link', { name: 'Open this measure in the score reader', exact: false }).click()
  await page.getByRole('region', { name: 'Selected measure preview', exact: true }).waitFor()
  await notation(second)

  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 })
    await noOverflow()
    await page.screenshot({ path: path.join(output, `reader-${width}.png`), fullPage: true })
    await nav().getByRole('link', { name: 'Library', exact: true }).click()
    await page.getByRole('link', { name: 'Open score', exact: false }).waitFor()
    await noOverflow()
    await page.getByText('Score options', { exact: true }).click()
    await noOverflow()
    await page.screenshot({ path: path.join(output, `library-${width}.png`), fullPage: true })
    await page.getByRole('link', { name: 'Open score', exact: false }).click()
    await notation(first)
    assert.equal(await page.evaluate(() => window.scrollY), 0, 'Opening a screen should reveal its heading and navigation')
  }
  console.log('PASS: marker uses original notation; library, reader and controls fit mobile, tablet and desktop')
  assert.deepEqual(errors, [])
  assert.equal((await context.request.get(`${origin}${score.source_file}`)).status(), 200)
  const failLibrary = route => route.request().method() === 'GET' ? route.fulfill({ status: 503, json: { detail: 'Test loading failure' } }) : route.continue()
  await page.route('**/api/scores/', failLibrary)
  await nav().getByRole('link', { name: 'Library', exact: true }).click()
  await page.getByRole('button', { name: 'Try again', exact: true }).waitFor()
  await page.unroute('**/api/scores/', failLibrary)
  await page.getByRole('button', { name: 'Try again', exact: true }).click()
  await page.getByRole('link', { name: 'Open score', exact: false }).waitFor()
  await page.getByText('Score options', { exact: true }).click()
  await page.getByRole('button', { name: 'Delete score', exact: true }).click()
  await page.getByRole('heading', { name: 'No scores yet', exact: true }).waitFor()
  assert.equal((await context.request.get(`${origin}${score.source_file}`)).status(), 404)
  assert.deepEqual(await json('practice-marks/'), [])
  console.log('PASS: score deletion removes its PDF and all attached records; no browser exceptions')
} catch (error) {
  await page.screenshot({ path: path.join(output, 'failure.png'), fullPage: true }).catch(() => {})
  throw error
} finally {
  if (score) await api(`scores/${score.id}/`, 'alex', { method: 'DELETE' }).catch(() => {})
  await browser.close()
}
