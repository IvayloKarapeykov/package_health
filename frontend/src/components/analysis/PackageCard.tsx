import { ExternalLink, Sparkles } from "lucide-react"

import { AlternativesList } from "@/components/analysis/AlternativesList"
import { FindingsList } from "@/components/analysis/FindingsList"
import { MetricsGrid } from "@/components/analysis/MetricsGrid"
import { ScoreMeter } from "@/components/analysis/ScoreMeter"
import { VerdictBadge } from "@/components/analysis/VerdictBadge"
import { VulnerabilityList } from "@/components/analysis/VulnerabilityList"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { ECOSYSTEM_BY_ID } from "@/lib/ecosystems"
import { formatBytes } from "@/lib/format"
import type { DependencyRef, PackageAssessment, RegistryInfo, VerdictSource } from "@/types/analysis"

const KIND_LABEL: Record<DependencyRef["kind"], string | null> = {
  direct: null,
  prod: "dependency",
  dev: "dev dependency",
  peer: "peer dependency",
  optional: "optional dependency",
}

interface PackageTitleProps {
  dependency: DependencyRef
  version?: string
  /** The package's registry page; unknown until its registry data has arrived. */
  href?: string
}

export function PackageTitle({ dependency, version, href }: PackageTitleProps) {
  const kind = KIND_LABEL[dependency.kind]
  const details = [
    version && `latest ${version}`,
    dependency.requested && `wants ${dependency.requested}`,
    kind,
  ].filter(Boolean)
  return (
    <div className="min-w-0">
      <div className="flex min-w-0 items-center gap-2">
        <a
          href={href}
          target="_blank"
          rel="noreferrer"
          className="group inline-flex min-w-0 items-center gap-1.5 font-mono text-base font-semibold aria-disabled:pointer-events-none [&[href]]:hover:underline"
          aria-disabled={!href}
        >
          <span className="truncate" title={dependency.name}>
            {dependency.name}
          </span>
          {href && (
            <ExternalLink className="size-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-60" aria-hidden />
          )}
        </a>
        <span className="glass-inset shrink-0 rounded-full px-2 py-px text-[10px] font-medium text-muted-foreground">
          {ECOSYSTEM_BY_ID[dependency.ecosystem].label}
        </span>
      </div>
      {details.length > 0 && (
        <p className="mt-0.5 font-mono text-xs text-muted-foreground">{details.join(" · ")}</p>
      )}
    </div>
  )
}

function VerdictSourceLabel({ source, confidence }: { source: VerdictSource; confidence: number | null }) {
  const percent = confidence != null ? `${Math.round(confidence * 100)}%` : null
  if (source === "rules") {
    return (
      <span title="Verdict decided by the rule-based health checks" className="font-mono text-[11px] text-muted-foreground">
        rules
      </span>
    )
  }
  const label = percent ? `jev · ${percent}` : "jev"
  const title = `Verdict decided by Jev (TypeSafe)${percent ? ` with ${percent} confidence` : ""}`
  return (
    <span title={title} className="font-mono text-[11px] text-muted-foreground">
      {label}
    </span>
  )
}

export function PackageCard({ assessment }: { assessment: PackageAssessment }) {
  const { dependency, signals, verdict } = assessment
  const registry = signals.registry
  const description = registry?.description ?? signals.repository?.description

  return (
    <Card className="animate-in fade-in-0 slide-in-from-bottom-1 duration-300">
      <CardHeader className="flex items-start justify-between gap-4">
        <PackageTitle dependency={dependency} version={registry?.latestVersion} href={registry?.registryUrl} />
        <div className="flex shrink-0 items-start gap-4">
          <ScoreMeter score={assessment.score} verdict={verdict} className="hidden sm:flex" />
          <div className="flex flex-col items-end gap-1">
            <VerdictBadge verdict={verdict} />
            <VerdictSourceLabel source={assessment.verdictSource} confidence={assessment.verdictConfidence} />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {description && <p className="text-sm text-muted-foreground">{description}</p>}

        <div className="space-y-2">
          <p className="flex items-start gap-2 text-sm font-medium">
            {assessment.explanationSource === "llm" && (
              <Sparkles className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-label="AI assessment" />
            )}
            {assessment.summary}
          </p>
          {assessment.reasons.length > 0 && (
            <ul className="list-disc space-y-1 pl-5 text-sm marker:text-muted-foreground">
              {assessment.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}
        </div>

        {registry && <MetricsGrid signals={signals} />}

        {registry && (
          <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-muted-foreground">
            {registryDetails(registry).map(([label, value]) => (
              <span key={label}>
                {label}: {value}
              </span>
            ))}
          </div>
        )}

        <VulnerabilityList vulnerabilities={signals.vulnerabilities?.vulnerabilities ?? []} />
        <AlternativesList alternatives={assessment.alternatives} />
        <FindingsList findings={assessment.findings} issues={signals.issues} />
      </CardContent>
    </Card>
  )
}

/** License plus whichever registry-specific extras this ecosystem exposes. */
function registryDetails(registry: RegistryInfo): [string, string][] {
  const details: [string, string | null][] = [
    ["license", registry.license ?? "none"],
    ["size", registry.unpackedSizeBytes != null ? formatBytes(registry.unpackedSizeBytes) : null],
    ["deps", registry.dependenciesCount != null ? String(registry.dependenciesCount) : null],
    ["types", registry.hasTypes != null ? (registry.hasTypes ? "yes" : "no") : null],
    ["maintainers", registry.maintainersCount != null ? String(registry.maintainersCount) : null],
  ]
  return details.filter((detail): detail is [string, string] => detail[1] != null)
}
