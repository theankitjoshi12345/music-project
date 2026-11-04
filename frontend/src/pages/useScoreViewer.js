import { useEffect, useState } from 'react'
import { initialPage, loadViewerData, pagePassages, sectionOptions } from './scoreViewerData'
import { requestExtraction } from './extractionRequest'

export default function useScoreViewer(user) {
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  const [location, setLocation] = useState(window.location.hash)
  const [focusedPassageId, setFocusedPassageId] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [extractionError, setExtractionError] = useState('')

  useEffect(() => {
    const updateLocation = () => setLocation(window.location.hash)
    window.addEventListener('hashchange', updateLocation)
    return () => window.removeEventListener('hashchange', updateLocation)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError('')
      setData(null)
      setExtracting(false)
      setExtractionError('')
      const query = new URLSearchParams(location.split('?')[1] || '')
      const scoreId = query.get('score')
      try {
        const result = await loadViewerData(scoreId, controller.signal, fetch, { 'X-Mock-User': user.id })
        if (!controller.signal.aborted) {
          setData(result)
          const startingPage = initialPage(result.passages, result.score?.page_count ?? 1, query.get('passage'))
          setPage(startingPage)
          setFocusedPassageId(Number(query.get('passage')) || result.passages.find((item) => item.page_number === startingPage)?.id || null)
          setLoading(false)
          const pdfNeedsPreviews = result.score?.source_file?.toLowerCase().endsWith('.pdf') &&
            (result.score.extraction_status === 'not_started' ||
              (result.score.extraction_status === 'complete' && !result.score.measure_layout_version) ||
              (result.score.extraction_status === 'failed' && query.get('extract') === '1'))
          if (pdfNeedsPreviews) {
            setExtracting(true)
            try {
              await requestExtraction(result.score.id, { 'X-Mock-User': user.id })
              const refreshed = await loadViewerData(result.score.id, controller.signal, fetch, { 'X-Mock-User': user.id })
              if (!controller.signal.aborted) setData(refreshed)
            } catch (failure) {
              if (!controller.signal.aborted) setExtractionError(failure.message)
            } finally {
              if (!controller.signal.aborted) setExtracting(false)
            }
          }
        }
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure.message || 'Unable to load the score.')
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    load()
    return () => controller.abort()
  }, [location, retry, user.id])

  useEffect(() => {
    if (!data?.score?.id || (!extracting && data.score.extraction_status !== 'processing')) return
    const controller = new AbortController()
    const timer = setInterval(async () => {
      try {
        const refreshed = await loadViewerData(data.score.id, controller.signal, fetch, { 'X-Mock-User': user.id })
        if (!controller.signal.aborted) {
          setData(refreshed)
          setExtractionError('')
        }
      } catch (failure) {
        if (!controller.signal.aborted) setExtractionError(failure.message)
      }
    }, 1500)
    return () => { clearInterval(timer); controller.abort() }
  }, [data?.score?.id, data?.score?.extraction_status, extracting, user.id])

  const passages = data?.passages ?? []
  const visible = pagePassages(passages, page)

  return {
    score: data?.score,
    isSample: data?.isSample ?? false,
    loading,
    error,
    page,
    visible,
    passages,
    extracting: extracting || data?.score?.extraction_status === 'processing',
    extractionError: extracting ? '' : extractionError || data?.score?.extraction_error || '',
    focusedPassageId,
    sections: sectionOptions(passages),
    currentSections: sectionOptions(visible),
    changePage(nextPage) {
      setPage(nextPage)
      setFocusedPassageId(passages.find((item) => item.page_number === nextPage)?.id || null)
    },
    changeSection(section) {
      const passage = passages.find((item) => item.section === section)
      if (passage) {
        setPage(passage.page_number)
        setFocusedPassageId(passage.id)
      }
    },
    jumpToMeasure(number) {
      const match = passages.find((passage) => passage.measure_number === number)
      if (!match) return 'Enter a measure number available in this score.'
      setPage(match.page_number)
      setFocusedPassageId(match.id)
      return ''
    },
    selectPassage(passage) {
      setPage(passage.page_number)
      setFocusedPassageId(passage.id)
    },
    retry() { setRetry((value) => value + 1) },
    async extractMeasures() {
      if (!data?.score?.id || extracting) return
      const scoreId = data.score.id
      setExtracting(true)
      setExtractionError('')
      try {
        await requestExtraction(scoreId, { 'X-Mock-User': user.id })
        const refreshed = await loadViewerData(scoreId, undefined, fetch, { 'X-Mock-User': user.id })
        setData((current) => current?.score.id === scoreId ? refreshed : current)
      } catch (failure) {
        setExtractionError(failure.message)
      } finally { setExtracting(false) }
    },
    async addPassage(values) {
      if (!data?.score?.id) throw new Error('Open a saved score before adding a measure.')
      const response = await fetch(`/api/scores/${data.score.id}/passages/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Mock-User': user.id }, body: JSON.stringify(values),
      })
      const passage = await response.json()
      if (!response.ok) throw new Error(passage.detail || passage.page_number?.[0] || passage.measure_number?.[0] || 'The measure could not be added.')
      setData((current) => ({ ...current, passages: [...current.passages.filter((item) => item.id !== passage.id), passage] }))
      setPage(passage.page_number)
      setFocusedPassageId(passage.id)
      return passage
    },
    async saveForPractice(passage) {
      const response = await fetch('/api/practice-marks/', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Mock-User': user.id }, body: JSON.stringify({ passage_id: passage.id }),
      })
      const mark = await response.json()
      if (!response.ok) throw new Error(mark.passage_id?.[0] || 'The practice mark could not be saved.')
      setData((current) => ({ ...current, passages: current.passages.map((item) => item.id === passage.id ? { ...item, is_marked_for_practice: true } : item) }))
      return mark
    },
  }
}
