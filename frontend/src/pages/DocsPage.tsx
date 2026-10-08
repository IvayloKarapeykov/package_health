import { Menu, X } from "lucide-react"
import { type RefObject, Suspense, useEffect, useRef, useState } from "react"
import { Navigate, useLocation, useParams } from "react-router"

import { DocsPager } from "@/components/docs/DocsPager"
import { DocsSearch } from "@/components/docs/DocsSearch"
import { DocsSidebar } from "@/components/docs/DocsSidebar"
import { DocsToc } from "@/components/docs/DocsToc"
import { SiteFooter } from "@/components/layout/SiteFooter"
import { mdxComponents } from "@/docs/mdxComponents"
import { DOC_BY_SLUG, DOC_PAGES } from "@/docs/nav"

export default function DocsPage() {
  const { slug = "" } = useParams()
  const page = DOC_BY_SLUG[slug]
  const contentRef = useRef<HTMLElement>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  useScrollToHash(contentRef)

  if (!page) return <Navigate to={`/docs/${DOC_PAGES[0].slug}`} replace />
  const { Content } = page

  return (
    <>
      <title>{`${page.title} · Docs · Package Health`}</title>
      <div className="mx-auto flex max-w-7xl gap-10 px-4 pt-24 pb-8 lg:px-6">
        <div className="sticky top-24 hidden max-h-[calc(100svh-7rem)] w-56 shrink-0 self-start overflow-y-auto pb-8 lg:block">
          <DocsSearch className="mb-6" />
          <DocsSidebar />
        </div>

        <main ref={contentRef} className="min-w-0 flex-1">
          <div className="space-y-3 lg:hidden">
            <DocsSearch />
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-expanded={menuOpen}
              className="glass-inset flex h-9 items-center gap-2 rounded-lg px-3 text-sm font-medium"
            >
              {menuOpen ? <X className="size-4" aria-hidden /> : <Menu className="size-4" aria-hidden />}
              {page.section}
            </button>
            {menuOpen && (
              <DocsSidebar onNavigate={() => setMenuOpen(false)} className="glass rounded-2xl p-3" />
            )}
          </div>

          <article key={page.slug} className="mx-auto max-w-3xl pt-8 lg:pt-0">
            <header className="border-b border-border pb-8">
              <p className="font-mono text-xs font-medium tracking-wider text-brand-blue uppercase">{page.section}</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">{page.title}</h1>
              <p className="mt-3 text-lg text-muted-foreground">{page.description}</p>
            </header>
            <Suspense fallback={<p className="mt-8 text-sm text-muted-foreground">Loading…</p>}>
              <Content components={mdxComponents} />
            </Suspense>
            <DocsPager slug={page.slug} />
          </article>
        </main>

        <DocsToc containerRef={contentRef} slug={page.slug} className="sticky top-24 hidden w-52 shrink-0 self-start xl:block" />
      </div>
      <SiteFooter />
    </>
  )
}

/** Scrolls to the URL's #section once it exists: pages load lazily, so it may not be there yet. */
function useScrollToHash(containerRef: RefObject<HTMLElement | null>) {
  const { hash, pathname } = useLocation()

  useEffect(() => {
    const container = containerRef.current
    const id = decodeURIComponent(hash.slice(1))
    if (!container || !id) return
    const scrollIfReady = () => {
      const target = document.getElementById(id)
      if (!target) return false
      target.scrollIntoView()
      return true
    }
    if (scrollIfReady()) return
    const observer = new MutationObserver(() => {
      if (scrollIfReady()) observer.disconnect()
    })
    observer.observe(container, { childList: true, subtree: true })
    const giveUp = setTimeout(() => observer.disconnect(), 5000)
    return () => {
      observer.disconnect()
      clearTimeout(giveUp)
    }
  }, [containerRef, hash, pathname])
}
