import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';
import path from 'path';

export default defineConfig({
  site: process.env.SITE_URL || 'https://cbop-dev.github.io',
  base: process.env.BASE_PATH !== undefined ? process.env.BASE_PATH : '/josephus-reader',
  integrations: [
    svelte(),
    sitemap()
  ],
  outDir: '../build',
  vite: {
    server: {
      fs: {
        allow: ['..']
      }
    },
    resolve: {
      alias: {
        '$lib': path.resolve('../src/lib'),
        '@shared': path.resolve('../shared'),
        '@src': path.resolve('../src')
      }
    }
  }
});
