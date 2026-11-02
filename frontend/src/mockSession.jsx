import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const storageKey = 'score-companion-mock-user-v1'
const MockSessionContext = createContext(null)

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

  useEffect(() => {
    try { localStorage.setItem(storageKey, userId) } catch { /* Browser storage is optional for the demo. */ }
  }, [userId])

  const value = useMemo(() => ({
    user: mockUsers.find((candidate) => candidate.id === userId) ?? mockUsers[0],
    users: mockUsers,
    setUserId,
  }), [userId])

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
  return { 'X-Mock-User': user.id }
}
