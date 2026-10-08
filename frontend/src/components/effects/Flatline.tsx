import { useId } from "react"

import { flatlinePath } from "@/lib/wavePath"
import { cn } from "@/lib/utils"

const WIDTH = 320
const HEIGHT = 56

export function Flatline({ className }: { className?: string }) {
  const gradientId = useId()
  return (
    <div className={cn("relative", className)}>
      <svg aria-hidden viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="block h-full w-full overflow-visible">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--brand-blue)" />
            <stop offset="45%" stopColor="var(--brand-cyan)" />
            <stop offset="75%" stopColor="var(--muted-foreground)" stopOpacity="0.45" />
            <stop offset="100%" stopColor="var(--muted-foreground)" stopOpacity="0.3" />
          </linearGradient>
        </defs>
        <path
          d={flatlinePath(WIDTH, HEIGHT, 34, 20)}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={2.25}
          strokeLinecap="round"
          pathLength={1}
          strokeDasharray={1}
          className="animate-draw drop-shadow-[0_0_6px_var(--brand-cyan)]"
        />
      </svg>
      {/* A last, fading blip where the trace goes flat. */}
      <span className="absolute top-1/2 right-0 grid size-2.5 translate-x-1/2 -translate-y-1/2 place-items-center">
        <span className="animate-ripple absolute inset-0 rounded-full border border-muted-foreground/60 [animation-delay:1.2s]" />
        <span className="size-2 rounded-full bg-muted-foreground/60" />
      </span>
    </div>
  )
}
