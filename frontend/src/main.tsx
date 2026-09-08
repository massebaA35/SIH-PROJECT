import { createRoot } from 'react-dom/client'
// @ts-ignore Vite resolves the JSX module and its named export at build time.
import { App } from './main.jsx'

createRoot(document.getElementById('app')!).render(<App />)