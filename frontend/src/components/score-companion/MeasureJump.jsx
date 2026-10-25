import { useId, useRef, useState } from 'react'

export default function MeasureJump({ onJump }) {
  const [value, setValue] = useState('')
  const [error, setError] = useState('')
  const fieldId = useId()
  const errorId = useId()
  const field = useRef(null)

  function submit(event) {
    event.preventDefault()
    const message = onJump(Number(value)) || ''
    setError(message)
    if (message) field.current?.focus()
  }

  return (
    <div>
      <form className="viewer-jump" onSubmit={submit}>
        <label htmlFor={fieldId}>Go to measure</label>
        <input ref={field} id={fieldId} type="number" min="1" step="1" required value={value} onChange={(event) => { setValue(event.target.value); setError('') }} aria-invalid={Boolean(error)} aria-describedby={error ? errorId : undefined} placeholder="e.g. 24" />
        <button type="submit">Go →</button>
      </form>
      {error && <p id={errorId} className="viewer-error" role="alert">{error}</p>}
    </div>
  )
}
