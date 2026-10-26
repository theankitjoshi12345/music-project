export default function ScreenHeading({ id, title, subtitle, byline }) {
  return (
    <header className="score-heading">
      {byline && <p className="viewer-byline">{byline}</p>}
      <h1 id={id}>{title}</h1>
      {subtitle && <p className="screen-subtitle">{subtitle}</p>}
    </header>
  )
}
