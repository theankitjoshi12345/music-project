export default function ScoreContext({ movement, instrument, sections = [], separator = ' • ' }) {
  const part = [movement, instrument].filter(Boolean).join(' • ')
  return <>{part}{sections.length > 0 && separator + 'Section ' + sections.join(', ')}</>
}
