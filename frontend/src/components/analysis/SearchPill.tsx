import { Search } from "lucide-react"

import { WaveLine } from "@/components/effects/WaveLine"
import { cn } from "@/lib/utils"

interface SearchPillProps {
  /** What is being (or was) analyzed, e.g. "express" or "pyproject.toml · 9 deps". */
  summary: string
  running: boolean
  failed?: boolean
  onClick: () => void
  className?: string
}

export function SearchPill({ summary, running, failed = false, onClick, className }: SearchPillProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Open search"
      className={cn(
        "glass group flex h-11 max-w-[calc(100vw-10rem)] items-center gap-2.5 rounded-full pr-4 pl-3 text-sm transition hover:scale-[1.03] focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none",
        "animate-in fade-in-0 zoom-in-95 duration-300",
        className,
      )}
    >
      <span
        className={cn(
          "grid size-7 shrink-0 place-items-center rounded-full text-white",
          failed ? "bg-muted-foreground/60" : "bg-gradient-to-br from-brand-blue to-brand-cyan",
        )}
      >
        <Search className="size-3.5" aria-hidden />
      </span>
      <span className="truncate font-mono text-foreground/85">{summary}</span>
      {running && (
        <WaveLine gradient className="h-3.5 w-8 shrink-0" wavelength={200} amplitude={8} strokeWidth={2} duration="1.2s" />
      )}
    </button>
  )
}
