import { ArrowLeft, ArrowRight } from "lucide-react"
import { Link } from "react-router"

import { DOC_PAGES } from "@/docs/nav"

export function DocsPager({ slug }: { slug: string }) {
  const index = DOC_PAGES.findIndex((page) => page.slug === slug)
  const previous = DOC_PAGES[index - 1]
  const next = DOC_PAGES[index + 1]
  return (
    <nav aria-label="Previous and next page" className="mt-16 grid gap-3 border-t border-border pt-8 sm:grid-cols-2">
      {previous ? (
        <Link to={`/docs/${previous.slug}`} className="glass group rounded-xl px-4 py-3 transition hover:-translate-y-px">
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <ArrowLeft className="size-3" aria-hidden /> Previous
          </span>
          <span className="mt-0.5 block font-medium">{previous.title}</span>
        </Link>
      ) : (
        <span />
      )}
      {next && (
        <Link to={`/docs/${next.slug}`} className="glass group rounded-xl px-4 py-3 text-right transition hover:-translate-y-px">
          <span className="flex items-center justify-end gap-1 text-xs text-muted-foreground">
            Next <ArrowRight className="size-3" aria-hidden />
          </span>
          <span className="mt-0.5 block font-medium">{next.title}</span>
        </Link>
      )}
    </nav>
  )
}
