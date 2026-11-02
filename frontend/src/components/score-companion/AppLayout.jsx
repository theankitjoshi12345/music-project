import MockUserControl from '../../MockUserControl'

const defaultNavigation = [
  { href: '#/score-library', label: 'Score library' },
  { href: '#/practice-review', label: 'Practice review' },
]

export function AppHeader({ status = 'Score Companion', homeHref = '#/score-library', activeHref }) {
  return (
    <header className="score-topbar">
      <a className="viewer-brand" href={homeHref}><span aria-hidden="true">♫</span> Score Companion</a>
      <nav className="viewer-primary-nav" aria-label="Main navigation"><a href="#/score-library" aria-current={activeHref === '#/score-library' ? 'page' : undefined}>Library</a><a href="#/practice-review" aria-current={activeHref === '#/practice-review' ? 'page' : undefined}>Practice</a></nav>
      <div className="viewer-header-meta">
        <MockUserControl />
        <span className="viewer-status"><i aria-hidden="true" /> {status}</span>
      </div>
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
      <AppHeader status={status} activeHref={activeHref} />
      <div className="viewer-layout">
        {navigation && <SidebarNavigation items={navigation} activeHref={activeHref} />}
        <section className="score-content" aria-labelledby={headingId} aria-busy={busy}>
          {children}
        </section>
      </div>
    </main>
  )
}
