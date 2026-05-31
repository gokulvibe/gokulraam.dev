import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';
import node from '@astrojs/node';
import cloudflare from '@astrojs/cloudflare';

// Pick the adapter at build time. Cloudflare Pages sets CF_PAGES=1 in its
// build environment; locally we default to Node so `npm run build` keeps
// working on your laptop without spinning up Wrangler.
const isCloudflare = process.env.CF_PAGES === '1' || process.env.ASTRO_ADAPTER === 'cloudflare';

export default defineConfig({
  site: 'https://gokulraam.dev',
  output: 'hybrid',
  adapter: isCloudflare
    ? cloudflare({ platformProxy: { enabled: true } })
    : node({ mode: 'standalone' }),
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
