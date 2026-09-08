/// <reference types="vite/client" />

declare module '*.css' {
  const classes: Record<string, string>
  export default classes
}

declare module 'leaflet/dist/leaflet.css'
