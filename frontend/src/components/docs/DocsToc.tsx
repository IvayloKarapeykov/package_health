import { type RefObject, useEffect, useState } from "react"

import { cn } from "@/lib/utils"

interface Heading {
  id: string
  text: string
  level: 2 | 3
}

/** Outlines the article's h2/h3 headings and highlights the one being read. */
interface DocsTocProps {
  /** Stays mounted across pages, so the observer keeps watching while each article swaps in. */
  containerRef: RefObject<HTMLElement | null>
  slug: string
  className?: string
}

export function DocsToc({ containerRef, slug, className }: DocsTocProps) {
  const [headings, setHeadings] = useState<Heading[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)

  useEffect(() => {
    const article = containerRef.current?.querySelector("article")
    if (!article) return
    const collect = () =>
      setHeadings(
        [...article.querySelectorAll<HTMLElement>("h2[id], h3[id]")].map((element) => ({
          id: element.id,
          text: element.textContent ?? "",
          level: element.tagName === "H2" ? 2 : 3,
        })),
      )
    collect()
    // Pages load lazily, so headings appear after the first render.
    const mutations = new MutationObserver(collect)
    mutations.observe(article, { childList: true, subtree: true })
    return () => mutations.disconnect()
  }, [containerRef, slug])

  useEffect(() => {
    if (!headings.length) return
    const visible = new IntersectionObserver(
      (entries) => {
        const top = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
        if (top) setActiveId(top.target.id)
      },
      { rootMargin: "-96px 0px -65% 0px" },
    )
    for (const { id } of headings) {
      const element = document.getElementById(id)
      if (element) visible.observe(element)
    }
    return () => visible.disconnect()
  }, [headings])

  if (!headings.length) return null
  return (
    <nav aria-label="On this page" className={cn("text-sm", className)}>
      <p className="mb-3 text-xs font-semibold">On this page</p>
      <ul className="space-y-2 border-l border-border">
        {headings.map((heading) => (
          <li key={heading.id}>
            <a
              href={`#${heading.id}`}
              className={cn(
                "-ml-px block border-l py-0.5 transition-colors",
                heading.level === 3 ? "pl-6" : "pl-3",
                activeId === heading.id
                  ? "border-brand-blue text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              {heading.text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
