/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#070b14",
          900: "#0b1220",
          800: "#121a2f",
          700: "#1a2744",
        },
        saffron: {
          500: "#e87722",
          400: "#f08a3e",
        },
        cyan: {
          400: "#22d3ee",
          500: "#06b6d4",
        },
      },
      boxShadow: {
        glow: "0 0 40px rgba(6, 182, 212, 0.08)",
      },
    },
  },
  plugins: [],
};
