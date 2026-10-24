import { useEffect, useState } from 'react'
import './App.css'

const routes = {
  '/score-library': {
    title: 'Offline Score Library',
    owner: 'Logan Broussard',
    complexity: 'Easiest',
  },
  '/score-viewer': {
    title: 'Score Viewer & Navigation',
    owner: 'Ankit Joshi',
    complexity: 'Hardest',
  },
  '/measure-marker': {
    title: 'Measure Marker',
    owner: 'Matthew Pisani',
    complexity: 'Hard',
  },
  '/practice-review': {
    title: 'Practice Review',
    owner: 'Jonathan Dempsey',
    complexity: 'Medium',
  },
}

const defaultRoute = '/score-library'

function currentRoute() {
  const path = window.location.hash.replace('#', '')
  return routes[path] ? path : defaultRoute
}

function App() {
  const [route, setRoute] = useState(currentRoute)

  useEffect(() => {
    const handleHashChange = () => setRoute(currentRoute())
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const screen = routes[route]

  return (
    <main className="app-shell">
      <header>
        <p className="eyebrow">CMPS 453 · P#9 setup</p>
        <h1>Score Companion</h1>
        <p className="subtitle">Shared React + Django application shell</p>
      </header>

      <nav aria-label="Assigned screens">
        {Object.entries(routes).map(([path, item]) => (
          <a className={path === route ? 'active' : ''} href={`#${path}`} key={path}>
            {item.title}
          </a>
        ))}
      </nav>

      <section className="placeholder" aria-labelledby="screen-title">
        <p className="eyebrow">Placeholder route</p>
        <h2 id="screen-title">{screen.title}</h2>
        <dl>
          <div><dt>Owner</dt><dd>{screen.owner}</dd></div>
          <div><dt>Complexity</dt><dd>{screen.complexity}</dd></div>
        </dl>
        <p>
          This route is reserved for its owner. The approved Figma design has not
          been implemented in the P#9 app shell.
        </p>
      </section>

      <footer>
        API health check: <code>GET /api/health/</code>
      </footer>
    </main>
  )
}

export default App
