import { History, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { formatTimeAgo } from "@/lib/format"
import type { SearchSummary } from "@/lib/searchHistory"
import { cn } from "@/lib/utils"
import { VERDICT_META } from "@/lib/verdict"

interface RecentSearchesProps {
  searches: SearchSummary[]
  onOpen: (id: string) => void
  onRemove: (id: string) => void
  onClear: () => void
  className?: string
}

/** Past searches saved in this browser; opening one shows its saved report instantly. */
export function RecentSearches({ searches, onOpen, onRemove, onClear, className }: RecentSearchesProps) {
  if (!searches.length) return null
  return (
    <section aria-label="Recent searches" className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between pl-1 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <History className="size-3.5" aria-hidden /> Recent
        </span>
        <Button type="button" variant="link" size="xs" className="h-auto px-0 text-muted-foreground" onClick={onClear}>
          Clear
        </Button>
      </div>
      <ul className="flex flex-wrap gap-1.5">
        {searches.map((search) => {
          const verdict = VERDICT_META[search.verdict]
          return (
            <li
              key={search.id}
              className="glass-inset group flex items-center rounded-full text-xs transition hover:border-brand-cyan/60"
            >
              <button
                type="button"
                onClick={() => onOpen(search.id)}
                title={`${verdict.label} · saved ${formatTimeAgo(search.savedAt)}`}
                className="flex items-center gap-2 rounded-full py-1 pr-1 pl-2.5 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                <span className={cn("size-1.5 shrink-0 rounded-full", verdict.fillClass)} aria-hidden />
                <span className="max-w-48 truncate font-mono text-foreground/85">{search.label}</span>
                <span className="text-muted-foreground">{search.detail}</span>
              </button>
              <button
                type="button"
                onClick={() => onRemove(search.id)}
                aria-label={`Remove ${search.label} from recent searches`}
                className="mr-1 grid size-5 place-items-center rounded-full text-muted-foreground opacity-40 transition group-hover:opacity-100 hover:bg-foreground/10 hover:text-foreground focus-visible:opacity-100 focus-visible:outline-none"
              >
                <X className="size-3" aria-hidden />
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
