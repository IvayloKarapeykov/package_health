import path from 'node:path'
import mdx from '@mdx-js/rollup'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import rehypeSlug from 'rehype-slug'
import remarkGfm from 'remark-gfm'
import { defineConfig, type Rollup } from 'vite'

interface HastNode {
  type: string
  tagName?: string
  data?: { meta?: string }
  properties?: Record<string, unknown>
  children?: HastNode[]
}

// Keeps a code fence's meta (```json title="package.json") as data-meta, so docs can show it as the file name.
function rehypeCodeMeta() {
  const walk = (node: HastNode) => {
    if (node.tagName === 'code' && node.data?.meta) node.properties = { ...node.properties, dataMeta: node.data.meta }
    node.children?.forEach(walk)
  }
  return walk
}

const mdxPlugin = mdx({ remarkPlugins: [remarkGfm], rehypePlugins: [rehypeSlug, rehypeCodeMeta] })
type TransformHook = (this: Rollup.TransformPluginContext, code: string, id: string) => Rollup.TransformResult | Promise<Rollup.TransformResult>
const compileMdx = mdxPlugin.transform as TransformHook

export default defineConfig({
  plugins: [
    {
      ...mdxPlugin,
      enforce: 'pre',
      // Leave ?raw and other query imports to Vite: docs search reads the MDX source as text.
      transform(code, id) {
        return id.includes('?') ? null : compileMdx.call(this, code, id)
      },
    },
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
