import { PackageTitle } from "@/components/analysis/PackageCard"
import { WaveTrack, type WaveStop } from "@/components/effects/WaveTrack"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { ECOSYSTEM_BY_ID } from "@/lib/ecosystems"
import { ASSESSMENT_STEPS, stepIndex } from "@/lib/steps"
import type { AssessmentStep, DependencyRef } from "@/types/analysis"

// How far past the current bead the wave reaches, as a fraction of one step: it "flows ahead".
const LEAD = 0.35

interface PackageProgressCardProps {
  dependency: DependencyRef
  step: AssessmentStep | undefined
}

export function PackageProgressCard({ dependency, step }: PackageProgressCardProps) {
  const current = stepIndex(step)
  const queued = current === -1
  const segments = ASSESSMENT_STEPS.length - 1
  const progress = queued ? 0 : Math.min(1, (current + LEAD) / segments)

  const stops: WaveStop[] = ASSESSMENT_STEPS.map((meta, index) => ({
    key: meta.id,
    label: meta.short,
    state: index < current ? "done" : index === current ? "active" : "pending",
  }))

  return (
    <Card aria-busy>
      <CardHeader className="flex items-start justify-between gap-4">
        <PackageTitle dependency={dependency} />
        <span className="shrink-0 font-mono text-xs text-muted-foreground tabular-nums">
          {queued ? "queued" : `${current + 1}/${ASSESSMENT_STEPS.length}`}
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground" aria-live="polite">
          {queued ? "Waiting for a free slot…" : `${ASSESSMENT_STEPS[current].label(ECOSYSTEM_BY_ID[dependency.ecosystem].label)}…`}
        </p>
        <WaveTrack progress={progress} stops={stops} />
      </CardContent>
    </Card>
  )
}
