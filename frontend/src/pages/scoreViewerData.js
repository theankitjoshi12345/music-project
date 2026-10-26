// Local illustration for an empty development database; never persisted as a score.
export const sampleScore = {
  id: null,
  title: 'Movement I',
  movement: 'Movement I',
  instrument: 'Percussion',
  page_count: 4,
  available_offline: false,
}

export const samplePassages = Array.from({ length: 40 }, (_, index) => ({
  id: 'sample-' + (index + 1),
  section: index < 16 ? 'A' : index < 24 ? 'B' : 'C',
  measure_number: index + 1,
  page_number: index < 16 ? 1 : Math.floor((index - 16) / 8) + 2,
}))

export function initialPage(passages, pageCount) {
  const target = passages.find((passage) => passage.section === 'B' && passage.measure_number === 24)
  return target?.page_number ?? passages[0]?.page_number ?? (pageCount > 0 ? 1 : 0)
}

export function pagePassages(passages, page) {
  return passages.filter((passage) => passage.page_number === page)
    .sort((a, b) => a.measure_number - b.measure_number || a.section.localeCompare(b.section))
}

export function sectionOptions(passages) {
  return [...new Set(passages.map((passage) => passage.section))]
}

export async function loadViewerData(scoreId, signal, request = fetch) {
  async function get(path) {
    const response = await request('/api/' + path, { signal })
    if (!response.ok) {
      throw new Error(response.status === 404 ? 'That score could not be found.' : 'The score service could not load this part.')
    }
    return response.json()
  }

  let id = scoreId
  if (!id) {
    const scores = await get('scores/')
    if (!scores.length) return { score: sampleScore, passages: samplePassages, isSample: true }
    id = scores[0].id
  }
  if (!/^\d+$/.test(String(id))) throw new Error('The score link needs a numeric score ID.')
  const [score, passages] = await Promise.all([
    get('scores/' + id + '/'), get('scores/' + id + '/passages/'),
  ])
  return { score, passages, isSample: false }
}
