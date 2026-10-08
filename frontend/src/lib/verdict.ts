import {
  CircleAlert,
  CircleCheck,
  CircleHelp,
  OctagonAlert,
  OctagonX,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react"

import type { Finding, Severity, Verdict } from "@/types/analysis"

export interface VerdictMeta {
  label: string
  headline: string
  icon: LucideIcon
  /** Classes for a tinted badge / pill. */
  badgeClass: string
  /** Text color class for icons and emphasis. */
  textClass: string
  /** Bar/fill color class. */
  fillClass: string
}

export const VERDICT_META: Record<Verdict, VerdictMeta> = {
  recommended: {
    label: "Recommended",
    headline: "Good to go",
    icon: CircleCheck,
    badgeClass: "bg-success/12 text-success ring-1 ring-success/25",
    textClass: "text-success",
    fillClass: "bg-success",
  },
  caution: {
    label: "Caution",
    headline: "Worth a closer look",
    icon: TriangleAlert,
    badgeClass: "bg-warning/15 text-warning-foreground ring-1 ring-warning/35",
    textClass: "text-warning-foreground",
    fillClass: "bg-warning",
  },
  avoid: {
    label: "Avoid",
    headline: "Action needed",
    icon: OctagonX,
    badgeClass: "bg-destructive/10 text-destructive ring-1 ring-destructive/25",
    textClass: "text-destructive",
    fillClass: "bg-destructive",
  },
  unknown: {
    label: "Unknown",
    headline: "Not enough data",
    icon: CircleHelp,
    badgeClass: "bg-muted text-muted-foreground ring-1 ring-border",
    textClass: "text-muted-foreground",
    fillClass: "bg-muted-foreground",
  },
}

/** Worst first: the order used for sorting and filtering. */
export const VERDICT_ORDER: Verdict[] = ["avoid", "caution", "recommended", "unknown"]

export const SEVERITY_CLASS: Record<Severity, string> = {
  critical: "bg-destructive text-white",
  high: "bg-destructive/15 text-destructive",
  moderate: "bg-warning/20 text-warning-foreground",
  low: "bg-muted text-muted-foreground",
  unknown: "bg-muted text-muted-foreground",
}

export const IMPACT_ICON: Record<Finding["impact"], { icon: LucideIcon; className: string }> = {
  positive: { icon: CircleCheck, className: "text-success" },
  negative: { icon: CircleAlert, className: "text-warning-foreground" },
  critical: { icon: OctagonAlert, className: "text-destructive" },
}
