import { useEffect, useRef } from 'react'
import { themes, useTheme } from '../../themeContext'

export default function ThemePicker() {
  const { theme, setTheme } = useTheme()
  const disclosure = useRef(null)
  useEffect(() => {
    function closeOutside(event) {
      if (!disclosure.current?.contains(event.target)) disclosure.current.open = false
    }
    document.addEventListener('pointerdown', closeOutside)
    return () => document.removeEventListener('pointerdown', closeOutside)
  }, [])

  return <details className="theme-picker" ref={disclosure} onKeyDown={event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') event.stopPropagation()
    if (event.key === 'Escape') {
      disclosure.current.open = false
      disclosure.current.querySelector('summary').focus()
    }
  }}>
    <summary><span className="theme-picker__icon" aria-hidden="true">✦</span> Theme</summary>
    <div className="theme-picker__panel">
      <p>Find your color</p>
      <div role="group" aria-label="Color theme">
        {themes.map(item => <button key={item.id} type="button" aria-pressed={theme === item.id} onClick={() => {
          setTheme(item.id)
          disclosure.current.open = false
          disclosure.current.querySelector('summary').focus()
        }}>
          <span className={`theme-swatch theme-swatch--${item.id}`} aria-hidden="true" />
          <span><strong>{item.name}</strong><small>{item.description}</small></span>
          {theme === item.id && <span className="theme-picker__check" aria-hidden="true">✓</span>}
        </button>)}
      </div>
    </div>
  </details>
}
