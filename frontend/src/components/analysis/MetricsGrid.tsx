import { Archive, CalendarClock, Download, GitCommitHorizontal, CircleDot, Package, ShieldAlert, Star } from "lucide-react"
import type { LucideIcon } from "lucide-react"

import { describeAdoption, formatCompact, formatDate, formatRelativeDate } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { PackageSignals } from "@/types/analysis"

interface Metric {
  icon: LucideIcon
  label: string
  value: string
  hint?: string
  tone?: "default" | "bad"
}

function buildMetrics({ registry, adoption, repository, vulnerabilities }: PackageSignals): Metric[] {
  const affectingLatest = vulnerabilities?.vulnerabilities.filter((v) => v.affectsLatest).length ?? 0
  return [
    { icon: Download, ...describeAdoption(adoption) },
    {
      icon: Package,
      label: "Last release",
      value: formatRelativeDate(registry?.lastReleaseAt),
      hint: registry ? `${formatDate(registry.lastReleaseAt)} · ${registry.releasesLastYear} releases in 12 mo` : undefined,
    },
    {
      icon: GitCommitHorizontal,
      label: "Last commit",
      value: formatRelativeDate(repository?.lastCommitAt),
      hint: repository ? formatDate(repository.lastCommitAt) : "GitHub data unavailable",
    },
    { icon: Star, label: "GitHub stars", value: formatCompact(repository?.stars) },
    {
      icon: CircleDot,
      label: "Open issues + PRs",
      value: formatCompact(repository?.openIssues),
      hint: "GitHub counts open pull requests as issues",
    },
    {
      icon: ShieldAlert,
      label: "Vulns in latest",
      value: vulnerabilities ? String(affectingLatest) : "—",
      hint: vulnerabilities ? `${vulnerabilities.totalKnown} known across all versions` : undefined,
      tone: affectingLatest > 0 ? "bad" : "default",
    },
    {
      icon: CalendarClock,
      label: "First published",
      value: formatRelativeDate(registry?.createdAt),
      hint: registry ? `${registry.totalVersions} versions` : undefined,
    },
    {
      icon: Archive,
      label: "Repository",
      value: repository ? (repository.archived ? "Archived" : "Active") : "—",
      tone: repository?.archived ? "bad" : "default",
    },
  ]
}

export function MetricsGrid({ signals }: { signals: PackageSignals }) {
  return (
    <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {buildMetrics(signals).map(({ icon: Icon, label, value, hint, tone }) => (
        <div key={label} className="glass-inset rounded-xl px-3 py-2.5" title={hint}>
          <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Icon className="size-3.5" aria-hidden />
            {label}
          </dt>
          <dd className={cn("mt-0.5 font-mono text-sm font-medium tabular-nums", tone === "bad" && "text-destructive")}>
            {value}
          </dd>
        </div>
      ))}
    </dl>
  )
}
