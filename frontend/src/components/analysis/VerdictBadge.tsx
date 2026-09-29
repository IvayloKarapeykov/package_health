import { VERDICT_META } from "@/lib/verdict"
import { cn } from "@/lib/utils"
import type { Verdict } from "@/types/analysis"

interface VerdictBadgeProps {
  verdict: Verdict
  size?: "sm" | "lg"
  className?: string
}

export function VerdictBadge({ verdict, size = "sm", className }: VerdictBadgeProps) {
  const meta = VERDICT_META[verdict]
  const Icon = meta.icon
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-full font-medium whitespace-nowrap",
        size === "sm" ? "px-2.5 py-0.5 text-xs" : "px-3.5 py-1.5 text-sm",
        meta.badgeClass,
        className,
      )}
    >
      <Icon className={size === "sm" ? "size-3.5" : "size-4"} aria-hidden />
      {meta.label}
    </span>
  )
}
