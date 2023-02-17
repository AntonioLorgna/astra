/** @type {import('tailwindcss').Config} */
const withMT = require("@material-tailwind/react/utils/withMT");
module.exports = withMT({
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
    }
  },
  safelist: [
    {
      pattern: /bg-(red|orange|lime|green|blue|purple|blue)-(100)/, // You can display all the colors that you need
      // variants: ['lg', 'hover', 'focus', 'lg:hover'],      // Optional
    },
  ],
})
