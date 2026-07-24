import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12121a",
        paper: "#f7f6f3",
      },
    },
  },
  plugins: [],
};

export default config;
