import { useId, type CSSProperties } from "react"

import { sineWavePath } from "@/lib/wavePath"
import { cn } from "@/lib/utils"

const VIEW_WIDTH = 400
const VIEW_HEIGHT = 24

interface WaveLineProps {
  className?: string
  style?: CSSProperties
  /** Distance between crests, in view-box units (the SVG stretches to its container). */
  wavelength?: number
  amplitude?: number
  strokeWidth?: number
  /** Stroke with the brand blue → cyan gradient instead of `currentColor`. */
  gradient?: boolean
  /** Make the wave travel; `duration` is the time for one wavelength. */
  flowing?: boolean
  duration?: string
}

/** A single sine wave that fills its container, optionally flowing sideways. */
export function WaveLine({
  className,
  style,
  wavelength = 40,
  amplitude = 5,
  strokeWidth = 1.75,
  gradient = false,
  flowing = true,
  duration = "2.4s",
}: WaveLineProps) {
  const gradientId = useId()
  const flowStyle = { "--wavelength": `${wavelength}px`, "--wave-duration": duration } as CSSProperties

  return (
    <svg
      aria-hidden
      viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
      preserveAspectRatio="none"
      className={cn("block overflow-hidden", className)}
      style={style}
    >
      {gradient && (
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--brand-blue)" />
            <stop offset="100%" stopColor="var(--brand-cyan)" />
          </linearGradient>
        </defs>
      )}
      <g className={cn(flowing && "animate-wave-flow")} style={flowStyle}>
        <path
          d={sineWavePath(VIEW_WIDTH, VIEW_HEIGHT, wavelength, amplitude)}
          fill="none"
          stroke={gradient ? `url(#${gradientId})` : "currentColor"}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </g>
    </svg>
  )
}
