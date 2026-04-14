/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        app: 'var(--app-bg)',
        sidebar: 'var(--sidebar-bg)',
        card: 'var(--card-bg)',
        primary: 'var(--text-primary)',
        secondary: 'var(--text-secondary)',
        accent: 'var(--accent-color)',
        border: 'var(--border-color)',
      },
    },
  },
  plugins: [],
}
