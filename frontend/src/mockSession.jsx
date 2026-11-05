import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const storageKey = 'score-companion-mock-user-v1'
const MockSessionContext = createContext(null)
let csrfToken = ''
let sessionRequest

function loadSession() {
  // React StrictMode can mount twice; establish one server identity first.
  sessionRequest ??= fetch('/api/session/', { credentials: 'same-origin' }).then(async response => {
    if (!response.ok) throw new Error('Your private workspace could not start. Please try again.')
    const session = await response.json()
    csrfToken = session.csrfToken || session.csrf_token || ''
    return session
  }).catch(error => { sessionRequest = undefined; throw error })
  return sessionRequest
}

export const mockUsers = [
  { id: 'alex', name: 'Alex Rivera' },
  { id: 'sam', name: 'Sam Lee' },
]

function initialUserId() {
  try {
    const saved = localStorage.getItem(storageKey)
    return mockUsers.some((user) => user.id === saved) ? saved : mockUsers[0].id
  } catch {
    return mockUsers[0].id
  }
}

export function MockSessionProvider({ children }) {
  const [userId, setUserId] = useState(initialUserId)
  const [session, setSession] = useState(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    loadSession().then(data => { if (active) setSession(data) })
      .catch(failure => { if (active) setError(failure.message) })
    return () => { active = false }
  }, [attempt])

  useEffect(() => {
    try { localStorage.setItem(storageKey, userId) } catch { /* Browser storage is optional for the demo. */ }
  }, [userId])

  const value = useMemo(() => ({
    user: session?.auth_mode === 'session' ? { id: 'private-session', name: 'Your private workspace' } : mockUsers.find((candidate) => candidate.id === userId) ?? mockUsers[0],
    users: mockUsers,
    setUserId,
    authMode: session?.auth_mode,
  }), [userId, session])

  if (!session) return <main className="session-start" aria-busy={!error}>
    <h1>Score Companion</h1>
    {error ? <><p role="alert">{error}</p><button type="button" onClick={() => { setError(''); setAttempt(value => value + 1) }}>Try again</button></> : <p role="status">Opening your practice space…</p>}
  </main>
  return <MockSessionContext.Provider value={value}>{children}</MockSessionContext.Provider>
}

export function useMockSession() {
  const session = useContext(MockSessionContext)
  return session ?? {
    user: mockUsers[0],
    users: mockUsers,
    setUserId: () => {},
  }
}

export function mockUserHeaders(user) {
  return { 'X-Mock-User': user.id, ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}) }
}
