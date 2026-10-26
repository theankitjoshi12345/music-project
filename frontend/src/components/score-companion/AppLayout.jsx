const defaultNavigation = [
  { href: '#/score-library', label: 'Score library' },
  { href: '#/practice-review', label: 'Practice review' },
]

export function AppHeader({ status = 'Score Companion', homeHref = '#/score-library' }) {
  return (
    <header className="score-topbar">
      <a className="viewer-brand" href={homeHref}><span aria-hidden="true">♫</span> Score Companion</a>
      <span className="viewer-status"><i aria-hidden="true" /> {status}</span>
    </header>
  )
}

export function SidebarNavigation({ items = defaultNavigation, activeHref }) {
  return (
    <aside className="score-sidebar" aria-label="Main navigation">
      {items.map(({ href, label }) => (
        <a key={href} href={href} aria-current={href === activeHref ? 'page' : undefined}>{label}</a>
      ))}
    </aside>
  )
}

export default function AppLayout({ children, status, navigation, activeHref, headingId, busy = false, className = '' }) {
  return (
    <main className={'score-companion ' + className}>
      <AppHeader status={status} />
      <div className="viewer-layout">
        <SidebarNavigation items={navigation} activeHref={activeHref} />
        <section className="score-content" aria-labelledby={headingId} aria-busy={busy}>
          {children}
        </section>
      </div>
    </main>
  )
}
