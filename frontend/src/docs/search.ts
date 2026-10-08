import GithubSlugger from "github-slugger"

import { DOC_PAGES } from "@/docs/nav"

const RAW_PAGES = import.meta.glob<string>("./pages/*.mdx", { query: "?raw", import: "default" })

export interface SearchEntry {
  slug: string
  pageTitle: string
  section: string
  /** null for the page's intro, before its first heading. */
  heading: string | null
  anchor: string | null
  text: string
}

export interface SearchResult extends SearchEntry {
  snippet: string
}

/** One entry per page section, read from the MDX source. Anchors match rehype-slug's heading ids. */
export async function loadSearchIndex(): Promise<SearchEntry[]> {
  const pages = await Promise.all(
    DOC_PAGES.map(async (page) => ({ page, raw: await RAW_PAGES[`./pages/${page.slug}.mdx`]() })),
  )
  return pages.flatMap(({ page, raw }) => {
    const entries: SearchEntry[] = []
    const slugger = new GithubSlugger()
    let current = { heading: null as string | null, anchor: null as string | null, lines: [] as string[] }
    const flush = () =>
      entries.push({ slug: page.slug, pageTitle: page.title, section: page.section, ...current, text: current.lines.join(" ") })

    let inFence = false
    for (const line of raw.split("\n")) {
      if (line.startsWith("```")) inFence = !inFence
      if (inFence || line.startsWith("```")) continue
      const heading = line.match(/^#{2,3}\s+(.+)$/)
      if (heading) {
        flush()
        current = { heading: heading[1], anchor: slugger.slug(heading[1]), lines: [] }
      } else {
        const text = plainText(line)
        if (text) current.lines.push(text)
      }
    }
    flush()
    return entries
  })
}

export function searchDocs(index: SearchEntry[], query: string, limit = 8): SearchResult[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean)
  if (!terms.length) return []
  return index
    .map((entry) => {
      const title = entry.pageTitle.toLowerCase()
      const heading = entry.heading?.toLowerCase() ?? ""
      const text = entry.text.toLowerCase()
      let score = 0
      for (const term of terms) {
        if (title.includes(term)) score += entry.heading ? 2 : 4
        else if (heading.includes(term)) score += 3
        else if (text.includes(term)) score += 1
        else return null
      }
      return { ...entry, snippet: snippet(entry.text, terms), score }
    })
    .filter((result) => result !== null)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
}

function plainText(line: string): string {
  return line
    .replace(/<[^>]+>/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[`*|]/g, " ")
    .replace(/^[-\s]+$/, "")
    .replace(/\s+/g, " ")
    .trim()
}

function snippet(text: string, terms: string[]): string {
  const hits = terms.map((term) => text.toLowerCase().indexOf(term)).filter((index) => index >= 0)
  const at = hits.length ? Math.min(...hits) : 0
  const start = at > 40 ? text.lastIndexOf(" ", at - 40) + 1 : 0
  return (start > 0 ? "…" : "") + text.slice(start, start + 120) + (start + 120 < text.length ? "…" : "")
}
