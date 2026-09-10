/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0a0f1a',
        panel: '#101828',
        panel2: '#0d1420',
        line: '#22304a',
        muted: '#8291a8',
        accent: '#22d3c4',
        accent2: '#f2a93b',
        danger: '#f0616b',
        info: '#6f8bff',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
