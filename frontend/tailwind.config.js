/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#EEF5F3",
          100: "#C8DED5",
          200: "#A6CBC1",
          300: "#7BB5A9",
          400: "#4D9C8F",
          500: "#287C78",
          600: "#1F6663",
          700: "#164E52",
          800: "#103A3D",
          900: "#0A2829",
        },
        accent: {
          50:  "#F1F6F5",
          100: "#D7E8E3",
          200: "#B5D3CC",
          300: "#8DBBB1",
          400: "#5BA095",
          500: "#3E8A80",
          600: "#2F7268",
          700: "#245B54",
          800: "#1B4741",
          900: "#133330",
        },
        warn: {
          50:  "#FEF8EC",
          100: "#FCEDCB",
          200: "#F7DC9C",
          300: "#F0C566",
          400: "#E9AA3D",
          500: "#D98D1C",
          600: "#B8720F",
          700: "#91580C",
          800: "#6B3F0A",
          900: "#4A2A06",
        },
        surface: {
          page:  "#F3F7F4",      // legacy teal-tinted bg
          warm:  "#FBF7F3",      // new warm off-white (orange tint)
          warmHover: "#F5EDE3",  // warm hover
          card:  "#FFFFFF",
          hover: "#ECF3EF",
        },
        // ---------- DARK SCALE — pushed up one more visible notch ----------
        // slate-950 → page background (#1a2438) — soft navy
        // slate-900 → cards / raised surfaces (#232f45)
        // slate-800 → hover states / lighter surface (#2d3b52)
        // slate-700 → borders / stronger hover (#3a4a63)
        slate: {
          50:  "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#3a4a63",   // was #334155 — lighter border/hover
          800: "#2d3b52",   // was #1e293b — lifted card/table hover surface
          900: "#232f45",   // was #0f172a — card base
          950: "#1a2438",   // was #020617 — page background (much softer)
        },
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(120deg, #287C78 0%, #1F6663 55%, #164E52 100%)",
        "brand-tile":
          "linear-gradient(135deg, #287C78 0%, #164E52 100%)",
        "brand-tile-glow":
          "linear-gradient(135deg, #4D9C8F 0%, #287C78 100%)",
      },
    },
  },
  plugins: [],
};
