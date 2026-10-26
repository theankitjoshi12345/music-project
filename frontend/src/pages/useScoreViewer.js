import { useEffect, useState } from 'react'
import { initialPage, loadViewerData, pagePassages, samplePassages, sampleScore, sectionOptions } from './scoreViewerData'

export default function useScoreViewer() {
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  const [location, setLocation] = useState(window.location.hash)

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
      const scoreId = new URLSearchParams(location.split('?')[1] || '').get('score')
      try {
        const result = await loadViewerData(scoreId, controller.signal)
        if (!controller.signal.aborted) {
          setData(result)
          setPage(initialPage(result.passages, result.score.page_count))
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
    sections: sectionOptions(passages),
    currentSections: sectionOptions(visible),
    changePage: setPage,
    changeSection(section) {
      const passage = passages.find((item) => item.section === section)
      if (passage) setPage(passage.page_number)
    },
    jumpToMeasure(number) {
      const match = passages.find((passage) => passage.measure_number === number)
      if (!match) return 'Enter a measure number available in this score.'
      setPage(match.page_number)
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
