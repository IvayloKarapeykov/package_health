import { useCallback, useEffect, useState } from "react"

import { AnalyzeForm } from "@/components/analysis/AnalyzeForm"
import { ErrorState } from "@/components/analysis/ErrorState"
import { RecentSearches } from "@/components/analysis/RecentSearches"
import { ResultsView } from "@/components/analysis/ResultsView"
import { SearchPill } from "@/components/analysis/SearchPill"
import { WaveBorder } from "@/components/effects/WaveBorder"
import { AppBackground } from "@/components/layout/AppBackground"
import { Hero } from "@/components/layout/Hero"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Wordmark } from "@/components/layout/Wordmark"
import { useAnalysis } from "@/hooks/useAnalysis"
import { useSearchHistory } from "@/hooks/useSearchHistory"
import { useTheme } from "@/hooks/useTheme"
import { saveSearch } from "@/lib/searchHistory"
import { cn } from "@/lib/utils"
import type { AnalysisRequest, Ecosystem } from "@/types/analysis"

const SEARCH_RADIUS_PX = 24

function describeRequest(request: AnalysisRequest | null, manifest: string | null, plannedCount: number): string {
  if (!request) return "Search"
  if (request.mode === "package") return request.package
  const file = manifest ?? "dependency file"
  return plannedCount ? `${file} · ${plannedCount} deps` : file
}

export default function App() {
  const { theme, toggleTheme } = useTheme()
  const { state, analyze, restore, reset } = useAnalysis({ onReport: saveSearch })
  const history = useSearchHistory()
  const [lastRequest, setLastRequest] = useState<AnalysisRequest | null>(null)
  const [searchOpen, setSearchOpen] = useState(true)

  const running = state.status === "running"
  const active = state.status !== "idle"
  const failed = state.status === "error"
  // Once an analysis starts the panel folds into a pill so the results have the stage;
  // it comes back on demand, or when the input itself needs fixing.
  const showPanel = !active || searchOpen || state.error?.kind === "invalid"

  const handleAnalyze = useCallback(
    (request: AnalysisRequest) => {
      setLastRequest(request)
      setSearchOpen(false)
      void analyze(request)
    },
    [analyze],
  )

  const handleRetry = useCallback(() => {
    if (lastRequest) handleAnalyze(lastRequest)
  }, [handleAnalyze, lastRequest])

  const handleOpenSaved = useCallback(
    (id: string) => {
      const saved = history.load(id)
      if (!saved) return
      setLastRequest(saved.request)
      setSearchOpen(false)
      restore(saved)
    },
    [history, restore],
  )

  const handleSwitchEcosystem = useCallback(
    (ecosystem: Ecosystem) => {
      if (lastRequest?.mode === "package") handleAnalyze({ ...lastRequest, ecosystem })
    },
    [handleAnalyze, lastRequest],
  )

  const handleReset = useCallback(() => {
    reset()
    setSearchOpen(true)
  }, [reset])

  useEffect(() => {
    if (!active || !searchOpen) return
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSearchOpen(false)
    }
    window.addEventListener("keydown", closeOnEscape)
    return () => window.removeEventListener("keydown", closeOnEscape)
  }, [active, searchOpen])

  return (
    <div className="relative min-h-svh">
      <AppBackground />
      <Wordmark onClick={handleReset} className="fixed top-7 left-6 z-20" />
      {!showPanel && (
        <SearchPill
          summary={describeRequest(lastRequest, state.manifest, state.planned.length)}
          running={running}
          failed={failed}
          onClick={() => setSearchOpen(true)}
          className="fixed top-4 left-1/2 z-20 -translate-x-1/2"
        />
      )}
      <ThemeToggle theme={theme} onToggle={toggleTheme} className="fixed top-4 right-4 z-20" />

      <main
        className={cn(
          "mx-auto max-w-4xl px-4 pb-20 transition-[padding] duration-700 ease-out",
          active ? "pt-20" : "pt-[20svh]",
        )}
      >
        <Hero compact={active} />

        {/* Hidden rather than unmounted, so typed input survives folding the panel. */}
        <div hidden={!showPanel} className="animate-in fade-in-0 slide-in-from-top-2 duration-300">
          <WaveBorder
            radius={SEARCH_RADIUS_PX}
            energized={running}
            className={cn(
              "mx-auto transition-[margin,max-width] duration-700",
              active ? "mt-0 max-w-4xl" : "mt-10 max-w-2xl",
            )}
          >
            <div className="glass p-4 sm:p-5" style={{ borderRadius: SEARCH_RADIUS_PX }}>
              <AnalyzeForm running={running} onSubmit={handleAnalyze} />
            </div>
          </WaveBorder>
          <RecentSearches
            searches={history.searches}
            onOpen={handleOpenSaved}
            onRemove={history.remove}
            onClear={history.clear}
            className={cn("mx-auto mt-5 px-1", active ? "max-w-4xl" : "max-w-2xl")}
          />
        </div>

        {state.error && (
          <div className={showPanel ? "mt-10" : "mt-2"}>
            <ErrorState
              failure={state.error}
              onRetry={lastRequest ? handleRetry : undefined}
              onEdit={showPanel ? undefined : () => setSearchOpen(true)}
            />
          </div>
        )}

        {active && !failed && (
          <div className={showPanel ? "mt-10" : "mt-2"}>
            <ResultsView
              state={state}
              request={lastRequest}
              onSwitchEcosystem={handleSwitchEcosystem}
              onRerun={handleRetry}
            />
          </div>
        )}
      </main>
    </div>
  )
}
