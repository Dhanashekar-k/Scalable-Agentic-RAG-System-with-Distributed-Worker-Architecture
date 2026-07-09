/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'claude-bg':             '#F7F6F3',
        'claude-surface':        '#FFFFFF',
        'claude-border':         '#E8E6E0',
        'claude-text':           '#1A1A1A',
        'claude-text-secondary': '#5C5C5C',
        'claude-text-tertiary':  '#9A9A9A',
        'claude-accent':         '#D97757',
        'claude-accent-hover':   '#C4673F',
        'claude-code-bg':        '#F2F1EE',
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        sans:    ['DM Sans', 'system-ui', 'sans-serif'],
        mono:    ['DM Mono', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        claude: '0.75rem',
      },
      boxShadow: {
        claude:    '0 1px 3px 0 rgba(0,0,0,0.06)',
        'claude-lg': '0 4px 16px -2px rgba(0,0,0,0.08)',
        'claude-xl': '0 8px 32px -4px rgba(0,0,0,0.10)',
      },
    },
  },
  plugins: [],
}
