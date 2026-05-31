import { defineConfig, passthroughImageService } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import react from '@astrojs/react';
import node from '@astrojs/node';
import cloudflare from '@astrojs/cloudflare';

// Adapter selection:
//   Default = Cloudflare (so `astro build` on Cloudflare Pages / Workers Builds
//   always produces a Worker-compatible bundle, even without a special env var).
//   Override to Node by exporting ASTRO_ADAPTER=node before building — useful
//   if you want to test the production build locally against the Node runtime.
//
//   Note: `astro dev` (the local dev server) doesn't use the adapter, so this
//   selection only matters at build time.
const useNode = process.env.ASTRO_ADAPTER === 'node';

export default defineConfig({
  site: 'https://gokulraam.dev',
  output: 'hybrid',
  adapter: useNode
    ? node({ mode: 'standalone' })
    : cloudflare({ platformProxy: { enabled: true } }),
  integrations: [tailwind(), mdx(), react()],
  // Cloudflare Workers can't run Sharp (native binary). We don't use Astro's
  // <Image> component anyway — only raw <img> tags — so the passthrough
  // service is the right fit and silences the build warning.
  image: { service: passthroughImageService() },
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
