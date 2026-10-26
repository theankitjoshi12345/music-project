import './OfflineScoreLibrary.css'

const downloadedParts = [
  { title: 'Movement I — Percussion', pages: 4 },
  { title: 'Movement II — Percussion', pages: 4 },
]

function MusicNoteIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 3v12.2a3.5 3.5 0 1 1-2-3.16V7.1l-8 1.6v8.5a3.5 3.5 0 1 1-2-3.16V7l12-2.4V3z" />
    </svg>
  )
}

function OfflineScoreLibrary() {
  return (
    <div className="offline-library">
      <header className="offline-library__header">
        <a className="offline-library__brand" href="#/score-library">
          <MusicNoteIcon />
          <span>Score Companion</span>
        </a>
        <p className="offline-library__status">
          <span aria-hidden="true" />
          Offline ready
        </p>
      </header>

      <div className="offline-library__layout">
        <aside className="offline-library__sidebar">
          <nav aria-label="Score Companion">
            <a className="offline-library__nav-link is-active" href="#/score-library" aria-current="page">
              Score library
            </a>
            <a className="offline-library__nav-link" href="#/practice-review">
              Practice review
            </a>
          </nav>
        </aside>

        <main className="offline-library__content">
          <h1>Your offline score library</h1>
          <p className="offline-library__subtitle">
            Select the percussion score saved for rehearsal.
          </p>

          <section className="offline-library__parts" aria-labelledby="downloaded-parts-heading">
            <h2 id="downloaded-parts-heading">Your downloaded parts</h2>
            <ul>
              {downloadedParts.map((part) => (
                <li className="offline-library__part" key={part.title}>
                  <div className="offline-library__part-icon">
                    <MusicNoteIcon />
                  </div>
                  <div className="offline-library__part-details">
                    <h3>{part.title}</h3>
                    <p>PDF <span>·</span> {part.pages} pages <span>·</span> Available offline</p>
                  </div>
                  <button className="offline-library__open-button" type="button">
                    Open score <span aria-hidden="true">→</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </main>
      </div>
    </div>
  )
}

export default OfflineScoreLibrary
