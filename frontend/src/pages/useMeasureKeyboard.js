import { useEffect } from 'react'
import { adjacentMeasure } from './measureNavigation'

export default function useMeasureKeyboard(passages, selectedId, onSelect) {
  useEffect(() => {
    function navigate(event) {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return
      if (event.target?.isContentEditable || event.target?.closest?.('input, textarea, select, [role="combobox"]')) return
      const direction = event.key === 'ArrowLeft' ? -1 : event.key === 'ArrowRight' ? 1 : 0
      if (!direction || !passages.length) return
      event.preventDefault()
      const passage = adjacentMeasure(passages, selectedId, direction)
      if (passage) onSelect(passage)
    }
    window.addEventListener('keydown', navigate)
    return () => window.removeEventListener('keydown', navigate)
  }, [passages, selectedId, onSelect])
}
