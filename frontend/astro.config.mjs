import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';
import node from '@astrojs/node';

export default defineConfig({
  site: 'https://gokulraam.dev',
  // Most pages stay static (fast, free hosting). Pages that need fresh DB reads
  // (e.g. /til/<slug> for inline-edit liveness) opt out via `export const prerender = false`.
  output: 'hybrid',
  adapter: node({ mode: 'standalone' }),
  integrations: [tailwind(), mdx(), sitemap(), react()],
  markdown: {
    shikiConfig: {
      theme: 'github-dark-dimmed',
      wrap: true,
    },
  },
  vite: {
    define: {
      'import.meta.env.PUBLIC_API_BASE': JSON.stringify(
        process.env.PUBLIC_API_BASE ?? 'http://localhost:8000',
      ),
    },
  },
});
