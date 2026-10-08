import path from 'node:path'
import mdx from '@mdx-js/rollup'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import rehypeSlug from 'rehype-slug'
import remarkGfm from 'remark-gfm'
import { defineConfig } from 'vite'

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

export default defineConfig({
  plugins: [
    { enforce: 'pre', ...mdx({ remarkPlugins: [remarkGfm], rehypePlugins: [rehypeSlug, rehypeCodeMeta] }) },
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
