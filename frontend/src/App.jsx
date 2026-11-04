import { useEffect, useState } from 'react'
import ScoreViewer from './pages/ScoreViewer'
import OfflineScoreLibrary from './OfflineScoreLibrary.jsx'
import MeasureMarker from './MeasureMarker.jsx'
import PracticeReview from './PracticeReview.jsx'
import { useMockSession } from './mockSession'

const routes = new Set(['/score-library', '/score-viewer', '/measure-marker', '/practice-review'])
function currentRoute(hash) {
  const path = hash.replace('#', '').split('?')[0]
  return routes.has(path) ? path : '/score-library'
}

export default function App() {
  const { user } = useMockSession()
  const [hash, setHash] = useState(window.location.hash)
  const route = currentRoute(hash)
  const screenKey = `${user.id}:${hash}`

  useEffect(() => {
    const handleHashChange = () => setHash(window.location.hash)
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  if (route === '/measure-marker') return <MeasureMarker key={screenKey} />
  if (route === '/score-viewer') return <ScoreViewer key={screenKey} />
  if (route === '/practice-review') return <PracticeReview key={screenKey} />
  return <OfflineScoreLibrary key={screenKey} />
}
