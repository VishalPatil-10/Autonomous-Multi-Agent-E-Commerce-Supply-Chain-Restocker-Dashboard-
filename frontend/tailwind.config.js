/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          900: '#05080f',
          800: '#0a0e1a',
          700: '#0f1526',
          600: '#151d35',
          500: '#1c2644',
          400: '#2a3558',
        },
        accent: {
          cyan: '#22d3ee',
          violet: '#a78bfa',
          emerald: '#34d399',
          amber: '#fbbf24',
          rose: '#fb7185',
          blue: '#60a5fa',
        },
        text: {
          primary: '#f0f4ff',
          secondary: '#94a3c4',
          muted: '#5a6a8a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
