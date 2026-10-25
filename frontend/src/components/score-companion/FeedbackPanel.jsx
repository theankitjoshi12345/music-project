export default function FeedbackPanel({ title, children, actions, tone = 'status' }) {
  return (
    <section className="viewer-message" role={tone === 'error' ? 'alert' : 'status'}>
      {title && <h2>{title}</h2>}
      {children}
      {actions && <div className="feedback-actions">{actions}</div>}
    </section>
  )
}
