import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { MockSessionProvider } from './mockSession.jsx'
import { ThemeProvider } from './theme.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <MockSessionProvider>
        <App />
      </MockSessionProvider>
    </ThemeProvider>
  </StrictMode>,
)
