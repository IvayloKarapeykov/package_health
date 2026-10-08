import { FileCode2, PackageSearch, Search } from "lucide-react"
import { type Ref, useEffect, useMemo, useState } from "react"

import { ResultsView } from "@/components/analysis/ResultsView"
import { CodeBlock } from "@/components/editor/CodeBlock"
import { SectionHeading } from "@/components/landing/SectionHeading"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { type Demo, DEMOS } from "@/demo"
import { finishedState } from "@/hooks/useAnalysis"
import { ECOSYSTEM_BY_ID } from "@/lib/ecosystems"
import { detectManifestFormat } from "@/lib/manifestFormat"
import type { AnalysisRequest } from "@/types/analysis"

export function DemoSection({ ref }: { ref?: Ref<HTMLElement> }) {
  const [activeId, setActiveId] = useState(DEMOS[0].id)
  const [loaded, setLoaded] = useState<Record<string, Demo>>({})
  const demo = loaded[activeId]

  useEffect(() => {
    if (loaded[activeId]) return
    let cancelled = false
    void DEMOS.find((entry) => entry.id === activeId)!
      .load()
      .then((result) => {
        if (!cancelled) setLoaded((current) => ({ ...current, [activeId]: result }))
      })
    return () => {
      cancelled = true
    }
  }, [activeId, loaded])

  const state = useMemo(() => (demo ? finishedState(demo.report, null) : null), [demo])

  return (
    <section ref={ref} className="mx-auto max-w-6xl scroll-mt-16 px-4 pt-16 pb-24">
      <SectionHeading
        eyebrow="Live example"
        title="Real reports, not mockups"
        description="Three analyses run against the live registries, GitHub and OSV.dev, shown exactly as the app shows them."
      />

      <Tabs value={activeId} onValueChange={setActiveId} className="mt-10 items-center">
        <TabsList className="glass-inset max-sm:[&_svg]:hidden">
          {DEMOS.map((entry) => (
            <TabsTrigger key={entry.id} value={entry.id} className="font-mono text-xs">
              {entry.id === "log4j" ? <PackageSearch /> : <FileCode2 />}
              {entry.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="mt-8 grid min-h-[32rem] items-start gap-5 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        {demo && state ? (
          <>
            <div className="space-y-3">
              <DemoInput request={demo.request} />
              <p className="px-1 text-xs text-muted-foreground">Verdicts by Jev, explanations by the LLM.</p>
            </div>
            <div className="scrollbar-glass max-h-[40rem] overflow-y-auto overscroll-contain rounded-2xl pr-1 [mask-image:linear-gradient(to_bottom,black_calc(100%-4rem),transparent)] pb-16">
              <ResultsView state={state} request={demo.request} />
            </div>
          </>
        ) : (
          <p className="text-sm text-muted-foreground lg:col-span-2">Loading the example…</p>
        )}
      </div>
    </section>
  )
}

function DemoInput({ request }: { request: AnalysisRequest }) {
  if (request.mode === "manifest") {
    const format = detectManifestFormat(request.content)
    return (
      <CodeBlock
        title={request.filename ?? format?.name ?? "dependency file"}
        code={request.content}
        language={format?.syntax ?? "json"}
        lineNumbers
      />
    )
  }
  return (
    <div className="glass-inset flex h-12 items-center gap-3 rounded-xl px-3.5">
      <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
      <span className="min-w-0 truncate font-mono text-sm">{request.package}</span>
      {request.ecosystem !== "auto" && (
        <span className="glass-inset ml-auto shrink-0 rounded-full px-2 py-px text-[10px] font-medium text-muted-foreground">
          {ECOSYSTEM_BY_ID[request.ecosystem].label}
        </span>
      )}
    </div>
  )
}
