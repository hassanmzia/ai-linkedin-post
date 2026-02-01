/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        linkedin: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#0077B5',
          600: '#006097',
          700: '#004d79',
        },
      },
    },
  },
  plugins: [],
};
