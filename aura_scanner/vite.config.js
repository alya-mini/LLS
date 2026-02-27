import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: {
    assetsInlineLimit: 10000000,
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
});
