import { ChevronDown, CircleAlert, CircleCheck, OctagonAlert } from "lucide-react"
import { useState } from "react"

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"
import type { Finding, SourceIssue } from "@/types/analysis"

const IMPACT_ICON = {
  positive: { icon: CircleCheck, className: "text-success" },
  negative: { icon: CircleAlert, className: "text-warning-foreground" },
  critical: { icon: OctagonAlert, className: "text-destructive" },
} as const

interface FindingsListProps {
  findings: Finding[]
  issues: SourceIssue[]
}

export function FindingsList({ findings, issues }: FindingsListProps) {
  const [open, setOpen] = useState(false)
  if (!findings.length && !issues.length) return null

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground">
        <ChevronDown className={cn("size-3.5 transition-transform", open && "rotate-180")} aria-hidden />
        How the score was calculated ({findings.length} checks)
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ul className="mt-2 space-y-1">
          {findings.map((finding) => {
            const { icon: Icon, className } = IMPACT_ICON[finding.impact]
            return (
              <li key={finding.message} className="flex items-start gap-2 text-sm">
                <Icon className={cn("mt-0.5 size-3.5 shrink-0", className)} aria-hidden />
                <span className="flex-1">{finding.message}</span>
                {finding.penalty > 0 && (
                  <span className="font-mono text-xs text-muted-foreground tabular-nums">−{finding.penalty}</span>
                )}
              </li>
            )
          })}
          {issues.map((issue) => (
            <li key={`${issue.source}:${issue.message}`} className="flex items-start gap-2 text-sm text-muted-foreground">
              <span className="mt-0.5 shrink-0 rounded bg-muted px-1 font-mono text-[10px] uppercase">{issue.source}</span>
              <span>{issue.message}</span>
            </li>
          ))}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  )
}
