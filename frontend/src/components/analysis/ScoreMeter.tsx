import { VERDICT_META } from "@/lib/verdict"
import { cn } from "@/lib/utils"
import type { Verdict } from "@/types/analysis"

interface ScoreMeterProps {
  score: number | null
  verdict: Verdict
  className?: string
}

export function ScoreMeter({ score, verdict, className }: ScoreMeterProps) {
  if (score == null) return null
  return (
    <div className={cn("flex w-24 flex-col items-end gap-1", className)} title="Rule-based health score">
      <div className="font-mono text-sm tabular-nums">
        <span className="text-lg font-semibold">{score}</span>
        <span className="text-muted-foreground">/100</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full transition-[width] duration-500", VERDICT_META[verdict].fillClass)}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}
