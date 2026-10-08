import { WaveLine } from "@/components/effects/WaveLine"
import { cn } from "@/lib/utils"

export type StopState = "done" | "active" | "pending"

export interface WaveStop {
  key: string
  label: string
  state: StopState
}

interface WaveTrackProps {
  /** Fill level between 0 and 1. */
  progress: number
  /** Optional milestones spread evenly along the track. */
  stops?: WaveStop[]
  className?: string
}

export function WaveTrack({ progress, stops = [], className }: WaveTrackProps) {
  const reveal = Math.round(Math.min(1, Math.max(0, progress)) * 100)
  const position = (index: number) => (stops.length > 1 ? (index / (stops.length - 1)) * 100 : 0)

  return (
    <div className={cn("px-1.5", className)}>
      <div className="relative h-8">
        <WaveLine className="absolute inset-0 size-full text-foreground/12" duration="6s" />
        <WaveLine
          gradient
          strokeWidth={2.25}
          className="absolute inset-0 size-full transition-[clip-path] duration-700 ease-out drop-shadow-[0_0_6px_var(--brand-cyan)]"
          style={{ clipPath: `inset(-50% ${100 - reveal}% -50% 0)` }}
        />
        {stops.map((stop, index) => (
          <span
            key={stop.key}
            className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${position(index)}%` }}
          >
            <StopBead state={stop.state} />
          </span>
        ))}
      </div>

      {stops.length > 0 && (
        <div className="relative mt-1.5 h-4">
          {stops.map((stop, index) => (
            <span
              key={stop.key}
              className={cn(
                "absolute top-0 text-[11px] whitespace-nowrap transition-colors duration-300",
                index === 0 ? "translate-x-0" : index === stops.length - 1 ? "-translate-x-full" : "-translate-x-1/2",
                stop.state === "active" && "font-medium text-foreground",
                // Narrow screens only have room for the current step's label.
                stop.state !== "active" && "max-sm:hidden",
                stop.state === "done" && "text-muted-foreground",
                stop.state === "pending" && "text-muted-foreground/50",
              )}
              style={{ left: `${position(index)}%` }}
            >
              {stop.label}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function StopBead({ state }: { state: StopState }) {
  if (state === "active") {
    return (
      <span className="relative grid size-3 place-items-center">
        <span className="animate-ripple absolute inset-0 rounded-full border border-brand-cyan" />
        <span className="animate-ripple absolute inset-0 rounded-full border border-brand-cyan [animation-delay:0.9s]" />
        <span className="size-3 rounded-full bg-gradient-to-br from-brand-blue to-brand-cyan shadow-[0_0_10px_var(--brand-cyan)]" />
      </span>
    )
  }
  if (state === "done") {
    return <span className="block size-2.5 rounded-full bg-gradient-to-br from-brand-blue to-brand-cyan" />
  }
  return <span className="block size-2 rounded-full border border-foreground/25 bg-background" />
}
