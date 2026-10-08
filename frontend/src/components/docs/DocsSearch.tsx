import { CornerDownLeft, Search } from "lucide-react"
import { Dialog } from "radix-ui"
import { type KeyboardEvent, useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router"

import { loadSearchIndex, type SearchEntry, searchDocs } from "@/docs/search"
import { cn } from "@/lib/utils"

let indexPromise: Promise<SearchEntry[]> | null = null

export function DocsSearch({ className }: { className?: string }) {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const openOnShortcut = (event: globalThis.KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setOpen((current) => !current)
      }
    }
    window.addEventListener("keydown", openOnShortcut)
    return () => window.removeEventListener("keydown", openOnShortcut)
  }, [])

  const shortcut = navigator.platform.toLowerCase().includes("mac") ? "⌘K" : "Ctrl K"

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger
        className={cn(
          "glass-inset flex h-9 w-full items-center gap-2 rounded-lg px-3 text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none",
          className,
        )}
      >
        <Search className="size-4" aria-hidden />
        Search docs
        <kbd className="ml-auto font-mono text-[11px] text-muted-foreground/80">{shortcut}</kbd>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-[2px] data-[state=open]:animate-in data-[state=open]:fade-in-0 dark:bg-black/50" />
        <Dialog.Content
          aria-describedby={undefined}
          className="fixed top-[12svh] left-1/2 z-50 w-[calc(100%-2rem)] max-w-xl -translate-x-1/2 overflow-hidden rounded-2xl border border-border bg-popover text-popover-foreground shadow-2xl shadow-slate-900/20 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95"
        >
          <Dialog.Title className="sr-only">Search the docs</Dialog.Title>
          {open && <SearchPanel onDone={() => setOpen(false)} />}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

function SearchPanel({ onDone }: { onDone: () => void }) {
  const navigate = useNavigate()
  const [index, setIndex] = useState<SearchEntry[] | null>(null)
  const [query, setQuery] = useState("")
  const [selected, setSelected] = useState(0)

  useEffect(() => {
    indexPromise ??= loadSearchIndex()
    let cancelled = false
    void indexPromise.then((entries) => {
      if (!cancelled) setIndex(entries)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const results = useMemo(() => (index ? searchDocs(index, query) : []), [index, query])

  function go(result: SearchEntry) {
    navigate(`/docs/${result.slug}${result.anchor ? `#${result.anchor}` : ""}`)
    onDone()
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === "ArrowDown") setSelected((current) => Math.min(current + 1, results.length - 1))
    else if (event.key === "ArrowUp") setSelected((current) => Math.max(current - 1, 0))
    else if (event.key === "Enter" && results[selected]) go(results[selected])
    else return
    event.preventDefault()
  }

  return (
    <div onKeyDown={handleKeyDown}>
      <div className="flex items-center gap-3 border-b border-border px-4">
        <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        <input
          autoFocus
          value={query}
          onChange={(event) => {
            setQuery(event.target.value)
            setSelected(0)
          }}
          placeholder="Search the docs"
          aria-label="Search the docs"
          className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>
      <div className="max-h-[60svh] overflow-y-auto p-2">
        {!query.trim() ? (
          <p className="px-3 py-6 text-center text-sm text-muted-foreground">Search page titles, sections and text.</p>
        ) : !results.length ? (
          <p className="px-3 py-6 text-center text-sm text-muted-foreground">
            {index ? `No results for “${query}”` : "Loading…"}
          </p>
        ) : (
          <ul role="listbox" aria-label="Results">
            {results.map((result, position) => (
              <li key={`${result.slug}#${result.anchor}`} role="option" aria-selected={position === selected}>
                <button
                  type="button"
                  onClick={() => go(result)}
                  onMouseMove={() => setSelected(position)}
                  className={cn(
                    "flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left",
                    position === selected && "bg-muted",
                  )}
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {result.heading ?? result.pageTitle}
                      {result.heading && <span className="font-normal text-muted-foreground"> · {result.pageTitle}</span>}
                    </p>
                    {result.snippet && <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{result.snippet}</p>}
                  </div>
                  {position === selected && <CornerDownLeft className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" aria-hidden />}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
