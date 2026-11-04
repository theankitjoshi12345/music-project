export function adjacentMeasure(passages, selectedId, direction) {
  const index = passages.findIndex(passage => passage.id === selectedId)
  if (index < 0) return null
  return passages[index + direction] ?? null
}
