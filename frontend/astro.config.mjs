import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import react from '@astrojs/react';
import node from '@astrojs/node';
import cloudflare from '@astrojs/cloudflare';
// NOTE: @astrojs/sitemap removed — it doesn't currently support hybrid
// output + Cloudflare adapter (build crashes on routes with dynamic params).
// Re-add later with explicit customPages list, or once the upstream bug is
// fixed (see: github.com/withastro/astro/issues — search "sitemap hybrid").

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
  integrations: [tailwind(), mdx(), react()],
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
