/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: "#FBF8F3",
        "off-white": "#F7F3EC",
        espresso: "#1A1615",
        "dark-bronze": "#231F1D",
        "chocolate-brown": "#3D291D",
        "accent-brown": "#4A3525",
        taupe: "#786F68",
        gold: "#C9A24B",
        "gold-dark": "#9C7A3C",
      },
      fontFamily: {
        serif: ["Playfair Display", "serif"],
        "serif-display": ["Cormorant Garamond", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        xs: ["0.75rem", "1rem"],
        sm: ["0.875rem", "1.25rem"],
        base: ["1rem", "1.5rem"],
        lg: ["1.125rem", "1.75rem"],
        xl: ["1.25rem", "1.75rem"],
        "2xl": ["1.5rem", "2rem"],
        "3xl": ["1.875rem", "2.25rem"],
        "4xl": ["2.25rem", "2.5rem"],
        "5xl": ["3rem", "1"],
        "6xl": ["3.75rem", "1"],
        "7xl": ["4.5rem", "1"],
        "8xl": ["6rem", "1"],
      },
      spacing: {
        "safe": "max(1rem, env(safe-area-inset-left))",
      },
      backgroundImage: {
        "watermark": "radial-gradient(circle, rgba(26,22,21,0.05) 1px, transparent 1px)",
      },
      opacity: {
        "5": "0.05",
      },
    },
  },
  plugins: [],
};
