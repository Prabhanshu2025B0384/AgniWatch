import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './services/x402Client' // Initialize x402 interceptor
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
