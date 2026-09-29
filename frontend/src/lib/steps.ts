import type { AssessmentStep } from "@/types/analysis"

export interface StepMeta {
  id: AssessmentStep
  /** Short name shown under the wave track. */
  short: string
  /** What the branch is doing right now, given the registry's name (e.g. "PyPI"). */
  label: (registry: string) => string
}

/** Mirrors the order in which the backend's `assess_package` branch reports its steps. */
export const ASSESSMENT_STEPS: StepMeta[] = [
  { id: "registry", short: "Registry", label: (registry) => `Reading ${registry} metadata & adoption` },
  { id: "activity", short: "Activity", label: () => "Checking GitHub activity & OSV vulnerabilities" },
  { id: "scoring", short: "Score", label: () => "Scoring health signals" },
  { id: "deciding", short: "Verdict", label: () => "Deciding the verdict" },
  { id: "explaining", short: "Reasons", label: () => "Writing up the reasons" },
  { id: "alternatives", short: "Alternatives", label: (registry) => `Verifying alternatives on ${registry}` },
]

/** Index of the current step, or -1 while the branch is still queued. */
export function stepIndex(step: AssessmentStep | undefined): number {
  return step ? ASSESSMENT_STEPS.findIndex((meta) => meta.id === step) : -1
}
