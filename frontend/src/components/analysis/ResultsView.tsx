import { useMemo, useState } from "react"

import { DetectingCard } from "@/components/analysis/DetectingCard"
import { DetectionNote } from "@/components/analysis/DetectionNote"
import { PackageCard } from "@/components/analysis/PackageCard"
import { PackageProgressCard } from "@/components/analysis/PackageProgressCard"
import { ReportSummary } from "@/components/analysis/ReportSummary"
import { SavedResultNote } from "@/components/analysis/SavedResultNote"
import { Button } from "@/components/ui/button"
import type { AnalysisState } from "@/hooks/useAnalysis"
import { VERDICT_META, VERDICT_ORDER } from "@/lib/verdict"
import type { AnalysisRequest, DependencyRef, Ecosystem, PackageAssessment, Verdict } from "@/types/analysis"
import { dependencyKey } from "@/types/analysis"

type Filter = Verdict | "all"

type Row = { dependency: DependencyRef; assessment: PackageAssessment | undefined }

function countVerdicts(assessments: PackageAssessment[]): Record<Verdict, number> {
  const counts: Record<Verdict, number> = { recommended: 0, caution: 0, avoid: 0, unknown: 0 }
  for (const assessment of assessments) counts[assessment.verdict] += 1
  return counts
}

interface ResultsViewProps {
  state: AnalysisState
  request: AnalysisRequest | null
  /** Re-run an auto-detected package in another registry. */
  onSwitchEcosystem?: (ecosystem: Ecosystem) => void
  /** Run a saved (reopened) search again for fresh data. */
  onRerun?: () => void
}

export function ResultsView({ state, request, onSwitchEcosystem, onRerun }: ResultsViewProps) {
  const [filter, setFilter] = useState<Filter>("all")
  const { report, planned, progress, assessments, skipped, detection, savedAt } = state
  // "auto" looks the name up across registries before anything is planned.
  const detecting =
    state.status === "running" && !planned.length && request?.mode === "package" && request.ecosystem === "auto"

  // While streaming: plan order with placeholders. Once reduced: the report's worst-first order.
  const rows: Row[] = useMemo(
    () =>
      report
        ? report.assessments.map((assessment) => ({ dependency: assessment.dependency, assessment }))
        : planned.map((dependency) => ({ dependency, assessment: assessments[dependencyKey(dependency)] })),
    [report, planned, assessments],
  )

  const completed = Object.values(assessments)
  const counts = report?.counts ?? countVerdicts(completed)
  const visible = filter === "all" ? rows : rows.filter((row) => row.assessment?.verdict === filter)
  const showFilters = rows.length > 1

  return (
    <div className="space-y-4">
      {detecting && <DetectingCard spec={request.package} />}
      {(savedAt !== null || detection) && (
        <div className="space-y-1.5">
          {savedAt !== null && <SavedResultNote savedAt={savedAt} onRerun={onRerun} />}
          {detection && <DetectionNote detection={detection} onSwitch={onSwitchEcosystem} />}
        </div>
      )}

      {(planned.length > 1 || skipped.length > 0) && (
        <ReportSummary
          report={report}
          counts={counts}
          completed={completed.length}
          total={planned.length}
          skipped={skipped}
        />
      )}

      {showFilters && (
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by verdict">
          <FilterButton active={filter === "all"} onClick={() => setFilter("all")}>
            All ({rows.length})
          </FilterButton>
          {VERDICT_ORDER.filter((verdict) => counts[verdict] > 0).map((verdict) => (
            <FilterButton key={verdict} active={filter === verdict} onClick={() => setFilter(verdict)}>
              {VERDICT_META[verdict].label} ({counts[verdict]})
            </FilterButton>
          ))}
        </div>
      )}

      <div className="space-y-4">
        {visible.map(({ dependency, assessment }) =>
          assessment ? (
            <PackageCard key={dependencyKey(dependency)} assessment={assessment} />
          ) : (
            <PackageProgressCard
              key={dependencyKey(dependency)}
              dependency={dependency}
              step={progress[dependencyKey(dependency)]}
            />
          ),
        )}
      </div>
    </div>
  )
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <Button type="button" size="sm" variant={active ? "default" : "outline"} onClick={onClick} aria-pressed={active}>
      {children}
    </Button>
  )
}
