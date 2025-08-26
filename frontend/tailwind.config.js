export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        light: {
          bg: "#FFFFFF",
          text: {
            primary: "#2C3E50",
            secondary: "#7F8C8D",
          },
          card: "#FFFFFF",
          border: "#DEE2E6",
          success: "#27AE60",
          danger: "#E74C3C",
          accent: "#007BFF",
        },
        dark: {
          bg: "#121212",
          text: {
            primary: "#E0E0E0",
            secondary: "#B0B0B0",
          },
          card: "#444444",
          border: "#555555",
          success: "#00FF85",
          danger: "#FF4D6B",
          accent: "#1E90FF",
        },
      },
    },
  },
  plugins: [],
};
