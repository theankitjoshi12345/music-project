import './LoadingSkeleton.css'

export default function LoadingSkeleton({ label = 'Loading…', kind = 'cards', rows = 3 }) {
  return <div className={`loading-skeleton loading-skeleton--${kind}`} aria-busy="true" role="status">
    <span className="visually-hidden">{label}</span>
    <div aria-hidden="true">
      {kind === 'notation' ? <div className="skeleton-notation"><i /><i /><i /><i /><i /></div>
        : Array.from({ length: rows }, (_, index) => <div className="skeleton-card" key={index}>
          <div className="skeleton-line skeleton-line--title" /><div className="skeleton-line" /><div className="skeleton-line skeleton-line--short" />
        </div>)}
    </div>
  </div>
}
