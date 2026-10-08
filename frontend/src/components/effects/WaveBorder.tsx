import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react"

import { wavyRoundedRectPath } from "@/lib/wavePath"
import { cn } from "@/lib/utils"

interface WaveBorderProps {
  children: ReactNode
  className?: string
  /** Corner radius of the wrapped element, in px. */
  radius?: number
  /** Speeds the waves up, e.g. while work is in progress. */
  energized?: boolean
}

interface WaveLayer {
  offset: number
  amplitude: number
  wavelength: number
  speed: number // radians per second
  phaseShift: number
}

// Two out-of-phase layers give the outline depth.
const LAYERS: WaveLayer[] = [
  { offset: 7, amplitude: 3.5, wavelength: 46, speed: 1.1, phaseShift: 0 },
  { offset: 11, amplitude: 2.5, wavelength: 62, speed: -0.7, phaseShift: Math.PI / 2 },
]
const ENERGIZED_MULTIPLIER = 3.5

export function WaveBorder({ children, className, radius = 24, energized = false }: WaveBorderProps) {
  const gradientId = useId()
  const containerRef = useRef<HTMLDivElement>(null)
  const pathRefs = useRef<(SVGPathElement | null)[]>([])
  const gradientRef = useRef<SVGLinearGradientElement>(null)
  const energizedRef = useRef(energized)
  const [size, setSize] = useState({ width: 0, height: 0 })

  useEffect(() => {
    energizedRef.current = energized
  }, [energized])

  useLayoutEffect(() => {
    const element = containerRef.current
    if (!element) return
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setSize({ width, height })
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const { width, height } = size
    if (!width || !height) return

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    const phases = LAYERS.map((layer) => layer.phaseShift)
    let rotation = 0
    let previous = performance.now()
    let frame = 0

    const draw = (now: number) => {
      const seconds = Math.min((now - previous) / 1000, 0.1)
      previous = now
      const multiplier = energizedRef.current ? ENERGIZED_MULTIPLIER : 1

      LAYERS.forEach((layer, index) => {
        phases[index] += layer.speed * multiplier * seconds
        pathRefs.current[index]?.setAttribute(
          "d",
          wavyRoundedRectPath({ width, height, radius, ...layer, phase: phases[index] }),
        )
      })
      rotation = (rotation + 12 * multiplier * seconds) % 360
      gradientRef.current?.setAttribute("gradientTransform", `rotate(${rotation} ${width / 2} ${height / 2})`)

      if (!reducedMotion) frame = requestAnimationFrame(draw)
    }

    draw(previous)
    return () => cancelAnimationFrame(frame)
  }, [size, radius])

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <svg
        aria-hidden
        className="pointer-events-none absolute inset-0 size-full overflow-visible drop-shadow-[0_0_10px_var(--brand-cyan)]"
      >
        <defs>
          <linearGradient
            ref={gradientRef}
            id={gradientId}
            gradientUnits="userSpaceOnUse"
            x1={0}
            y1={0}
            x2={size.width}
            y2={size.height}
          >
            <stop offset="0%" stopColor="var(--brand-blue)" />
            <stop offset="50%" stopColor="var(--brand-cyan)" />
            <stop offset="100%" stopColor="var(--brand-blue)" />
          </linearGradient>
        </defs>
        {LAYERS.map((layer, index) => (
          <path
            key={layer.wavelength}
            ref={(element) => {
              pathRefs.current[index] = element
            }}
            fill="none"
            stroke={`url(#${gradientId})`}
            strokeWidth={index === 0 ? 1.75 : 1}
            strokeOpacity={index === 0 ? 0.9 : 0.45}
            strokeLinejoin="round"
          />
        ))}
      </svg>
      {children}
    </div>
  )
}
