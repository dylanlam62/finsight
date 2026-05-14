/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // HKT corporate blue
        brand: {
          50:  "#e6f0fa",
          100: "#cce0f5",
          200: "#99c1eb",
          300: "#66a2e0",
          400: "#3383d6",
          500: "#004FA3",
          600: "#003f82",
          700: "#002f62",
          800: "#002041",
          900: "#001021",
          950: "#000810",
        },
        // HKT gold accent
        gold: {
          400: "#FFD54F",
          500: "#FFB800",
          600: "#E6A600",
        },
        // Warm neutral palette — replaces cold Tailwind gray
        warm: {
          50:  "#FAFAF8",
          100: "#F5F3EE",
          200: "#EAE6DE",
          300: "#DDD8CE",
          400: "#C5BEB2",
          500: "#A09890",
          600: "#756E66",
          700: "#524D47",
          800: "#37322D",
          900: "#211D19",
          950: "#110E0B",
        },
      },
      fontFamily: {
        sans:  ["DM Sans", "system-ui", "sans-serif"],
        serif: ["Lora", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};
