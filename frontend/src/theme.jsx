import { useState } from 'react'
import { themes, ThemeContext } from './themeContext'
const storageKey = 'score-companion-theme-v1'

export function ThemeProvider({ children }) {
  const [theme, updateTheme] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey)
      return themes.some(item => item.id === saved) ? saved : 'violet'
    } catch { return 'violet' }
  })

  function setTheme(value) {
    if (!themes.some(item => item.id === value)) return
    updateTheme(value)
    try { localStorage.setItem(storageKey, value) } catch { /* The theme still works when storage is unavailable. */ }
  }

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>
}

