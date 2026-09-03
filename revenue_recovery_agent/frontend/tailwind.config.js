/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#070F1E',
          card: '#0D1A30',
          border: '#1E293B',
          blue: '#0082FF',
          cyan: '#00B9F1',
          emerald: '#10B981',
          amber: '#F59E0B',
          rose: '#F43F5E',
        }
      }
    },
  },
  plugins: [],
};
