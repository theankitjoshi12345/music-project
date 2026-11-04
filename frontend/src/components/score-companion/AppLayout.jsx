import MockUserControl from '../../MockUserControl'
import { useTheme } from '../../themeContext'
import ThemePicker from './ThemePicker'

const defaultNavigation = [
  { href: '#/score-library', label: 'Score library' },
  { href: '#/practice-review', label: 'Practice review' },
]

export function AppHeader({ status = 'Score Companion', homeHref = '#/score-library', activeHref }) {
  return (
    <header className="score-topbar">
      <a className="viewer-brand" href={homeHref} aria-label="Score Companion home"><img src="/favicon.svg" width="42" height="42" alt="" /><span>Score<br />Companion<span className="brand-spark" aria-hidden="true">✦</span></span></a>
      <nav className="viewer-primary-nav" aria-label="Main navigation"><a href="#/score-library" aria-current={activeHref === '#/score-library' ? 'page' : undefined}>Library</a><a href="#/practice-review" aria-current={activeHref === '#/practice-review' ? 'page' : undefined}>Practice review</a></nav>
      <div className="viewer-header-meta">
        <ThemePicker />
        <MockUserControl />
        <span className="visually-hidden">{status}</span>
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
  const { theme } = useTheme()
  return (
    <div className={'score-companion ' + className} data-color-theme={theme}>
      <AppHeader status={status} activeHref={activeHref} />
      <div className="viewer-layout">
        {navigation && <SidebarNavigation items={navigation} activeHref={activeHref} />}
        <main className="score-content" aria-labelledby={headingId} aria-busy={busy}>
          {children}
        </main>
      </div>
    </div>
  )
}
