import { useEffect, useState } from 'react'
import { initialPage, loadViewerData, pagePassages, samplePassages, sampleScore, sectionOptions } from './scoreViewerData'

export default function useScoreViewer() {
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  const [location, setLocation] = useState(window.location.hash)
  const [focusedPassageId, setFocusedPassageId] = useState(null)

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
      const query = new URLSearchParams(location.split('?')[1] || '')
      const scoreId = query.get('score')
      try {
        const result = await loadViewerData(scoreId, controller.signal)
        if (!controller.signal.aborted) {
          setData(result)
          const startingPage = initialPage(result.passages, result.score.page_count, query.get('passage'))
          setPage(startingPage)
          setFocusedPassageId(Number(query.get('passage')) || result.passages.find((item) => item.page_number === startingPage)?.id || null)
        }
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure.message || 'Unable to load the score.')
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    load()
    return () => controller.abort()
  }, [location, retry])

  const passages = data?.passages ?? []
  const visible = pagePassages(passages, page)

  return {
    score: data?.score,
    isSample: data?.isSample ?? false,
    loading,
    error,
    page,
    visible,
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
    retry() { setRetry((value) => value + 1) },
    showSample() {
      setData({ score: sampleScore, passages: samplePassages, isSample: true })
      setPage(2)
      setError('')
    },
  }
}
