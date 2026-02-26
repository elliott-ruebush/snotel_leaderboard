import { defineConfig } from 'vite'

export default defineConfig({
    base: './', // Vital for GitHub Pages to resolve paths correctly
    build: {
        outDir: 'dist',
    }
})
