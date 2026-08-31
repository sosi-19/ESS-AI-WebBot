import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
    process: {
      env: {
        NODE_ENV: "production",
      },
    },
  },

  build: {
    outDir: "widget-dist",
    emptyOutDir: true,

    lib: {
      entry: "src/widget/main.jsx",
      name: "ESSAIWidget",
      fileName: () => "ess-ai-widget.js",
      formats: ["iife"],
    },

    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
});