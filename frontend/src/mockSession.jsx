import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'

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

function GoogleSignIn({ clientId, onCredential }) {
  const button = useRef(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    let script = document.querySelector('script[data-score-google-signin]')
    const render = () => {
      if (!active || !window.google?.accounts?.id || !button.current) return
      window.google.accounts.id.initialize({
        client_id: clientId,
        auto_select: false,
        cancel_on_tap_outside: true,
        callback: ({ credential }) => onCredential(credential).catch(failure => setError(failure.message)),
      })
      window.google.accounts.id.renderButton(button.current, {
        type: 'standard', theme: 'outline', size: 'large', shape: 'pill', text: 'continue_with', width: 280,
      })
    }
    if (window.google?.accounts?.id) render()
    else {
      script ||= Object.assign(document.createElement('script'), {
        src: 'https://accounts.google.com/gsi/client', async: true, defer: true,
      })
      script.dataset.scoreGoogleSignin = 'true'
      script.addEventListener('load', render)
      script.addEventListener('error', () => active && setError('Google sign-in could not load. Check your connection and retry.'))
      if (!script.isConnected) document.head.appendChild(script)
    }
    return () => {
      active = false
      script?.removeEventListener('load', render)
    }
  }, [clientId, onCredential])

  return <main className="session-start google-sign-in">
    <img src="/favicon.svg" width="72" height="72" alt="" />
    <h1>Welcome to Score Companion</h1>
    <p>Sign in to keep your scores private and available when you return.</p>
    <div ref={button} aria-label="Google sign-in" />
    {error && <p role="alert">{error}</p>}
    <small>We use only your basic Google identity. We never request Drive, Gmail, or payment access.</small>
  </main>
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
    user: session?.auth_mode === 'google'
      ? { id: 'google-account', name: session.display_name, email: session.email }
      : session?.auth_mode === 'session'
        ? { id: 'private-session', name: 'Your private workspace' }
        : mockUsers.find((candidate) => candidate.id === userId) ?? mockUsers[0],
    users: mockUsers,
    setUserId,
    authMode: session?.auth_mode,
    async logout() {
      const response = await fetch('/api/auth/logout/', {
        method: 'POST', credentials: 'same-origin', headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
      })
      if (!response.ok) throw new Error('Sign out failed. Please try again.')
      window.google?.accounts?.id?.disableAutoSelect()
      sessionRequest = undefined
      const next = await loadSession()
      setSession(next)
    },
  }), [userId, session])

  if (!session) return <main className="session-start" aria-busy={!error}>
    <h1>Score Companion</h1>
    {error ? <><p role="alert">{error}</p><button type="button" onClick={() => { setError(''); setAttempt(value => value + 1) }}>Try again</button></> : <p role="status">Opening your practice space…</p>}
  </main>
  if (session.auth_mode === 'google' && !session.authenticated) {
    return <GoogleSignIn clientId={session.google_client_id} onCredential={async credential => {
      const response = await fetch('/api/auth/google/', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}) },
        body: JSON.stringify({ credential }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Google sign-in could not be verified.')
      csrfToken = data.csrfToken || data.csrf_token || csrfToken
      setSession(data)
    }} />
  }
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
