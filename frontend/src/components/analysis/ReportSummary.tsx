import { WaveTrack } from "@/components/effects/WaveTrack"
import { Card, CardContent } from "@/components/ui/card"
import { VERDICT_META, VERDICT_ORDER } from "@/lib/verdict"
import { cn } from "@/lib/utils"
import type { AnalysisReport, SkippedDependency, Verdict } from "@/types/analysis"

interface ReportSummaryProps {
  report: AnalysisReport | null
  counts: Record<Verdict, number>
  completed: number
  total: number
  skipped: SkippedDependency[]
}

/** Overall verdict and counts; shows live progress while branches are still running. */
export function ReportSummary({ report, counts, completed, total, skipped }: ReportSummaryProps) {
  const running = report === null
  const meta = report ? VERDICT_META[report.overallVerdict] : null
  const Icon = meta?.icon

  return (
    <Card>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            {Icon && meta && <Icon className={cn("mt-0.5 size-7 shrink-0", meta.textClass)} aria-hidden />}
            <div>
              <h2 className="text-lg font-semibold">
                {meta ? meta.headline : `Analyzing ${total} package${total === 1 ? "" : "s"} in parallel…`}
              </h2>
              <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                {report ? report.summary : "Checking each package's registry, GitHub and OSV.dev in parallel."}
              </p>
            </div>
          </div>
          <dl className="flex gap-2">
            {VERDICT_ORDER.filter((verdict) => verdict !== "unknown" || counts.unknown > 0).map((verdict) => (
              <div key={verdict} className={cn("min-w-20 rounded-lg px-3 py-2", VERDICT_META[verdict].badgeClass)}>
                <dt className="text-xs">{VERDICT_META[verdict].label}</dt>
                <dd className="font-mono text-xl font-semibold tabular-nums">{counts[verdict]}</dd>
              </div>
            ))}
          </dl>
        </div>

        {running && total > 0 && (
          <div className="space-y-1.5">
            <WaveTrack progress={completed / total} />
            <p className="font-mono text-xs text-muted-foreground tabular-nums">
              {completed} / {total} complete
            </p>
          </div>
        )}

        {skipped.length > 0 && (
          <details className="text-sm">
            <summary className="cursor-pointer text-muted-foreground">
              {skipped.length} dependenc{skipped.length === 1 ? "y" : "ies"} skipped
            </summary>
            <ul className="mt-2 space-y-1 font-mono text-xs">
              {skipped.map((item) => (
                <li key={item.name}>
                  {item.name} <span className="text-muted-foreground">({item.requested}) — {item.reason}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
      </CardContent>
    </Card>
  )
}
