import type { MDXContent } from "mdx/types"
import { lazy, type LazyExoticComponent } from "react"

type MdxModule = { default: MDXContent }

const PAGE_MODULES = import.meta.glob<MdxModule>("./pages/*.mdx")

export interface DocPage {
  slug: string
  title: string
  description: string
  section: string
  /** Loads the page's MDX on first render. */
  Content: LazyExoticComponent<MDXContent>
}

const SECTIONS: { title: string; pages: Omit<DocPage, "section" | "Content">[] }[] = [
  {
    title: "Getting started",
    pages: [
      { slug: "introduction", title: "Introduction", description: "What Package Health checks, and the ways to use it." },
      { slug: "quickstart", title: "Quickstart", description: "Check your first package in under a minute." },
      {
        slug: "how-verdicts-work",
        title: "How verdicts work",
        description: "How raw signals become recommended, caution or avoid.",
      },
    ],
  },
  {
    title: "Using the app",
    pages: [
      {
        slug: "checking-packages",
        title: "Checking packages",
        description: "Auto-detection, versions and your recent searches.",
      },
      { slug: "dependency-files", title: "Dependency files", description: "Every supported file, and what's read from it." },
      { slug: "reading-a-report", title: "Reading a report", description: "What each part of a report tells you." },
      { slug: "your-keys", title: "Your keys", description: "Use your own GitHub and OpenRouter keys, safely." },
    ],
  },
]

export const DOC_SECTIONS = SECTIONS.map((section) => ({
  title: section.title,
  pages: section.pages.map((page): DocPage => {
    const load = PAGE_MODULES[`./pages/${page.slug}.mdx`]
    if (!load) throw new Error(`Missing docs page: pages/${page.slug}.mdx`)
    return { ...page, section: section.title, Content: lazy(load) }
  }),
}))

export const DOC_PAGES = DOC_SECTIONS.flatMap((section) => section.pages)

export const DOC_BY_SLUG = Object.fromEntries(DOC_PAGES.map((page) => [page.slug, page]))
