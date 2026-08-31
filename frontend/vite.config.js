import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({

  plugins: [react()],

  build: {

    rollupOptions: {

      input: {
        main: "index.html",
        embed: "src/embed.jsx",
      },

      output: {

        format: "es",

        entryFileNames: (chunkInfo) => {

          if (chunkInfo.name === "embed") {
            return "embed.js";
          }

          return "assets/[name]-[hash].js";

        },

        chunkFileNames: "assets/[name]-[hash].js",

        assetFileNames: "assets/[name]-[hash][extname]",

      },

    },

  },

});