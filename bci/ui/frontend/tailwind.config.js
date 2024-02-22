/** @type {import('tailwindcss').Config} */
module.exports = {
  mode: "jit",
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./node_modules/flowbite/**/*.js",
  ],
  darkMode: ['selector'],
  plugins: [
    require('flowbite/plugin'),
  ],
  theme: {
    extend: {
      colors: {
        'light-sky': '#809BBF',
        'blue-sky': '#3C74A6',
        'horizon': '#F2DCC2',
        'sand': '#8C4D16',
        'bush': '#D97C2B',
        // Dark mode colors
        'dark-1': '#060314',
        'dark-2': '#090F26',
        'dark-3': '#101F38',
        'dark-4': '#172E4D',
        'dark-5': '#20385E',
        'dark-6': '#2649FC',
      },
    }
  }
}
