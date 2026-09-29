export interface WavePathOptions {
  width: number
  height: number
  /** Corner radius of the underlying rounded rectangle. */
  radius: number
  /** How far the outline sits outside the box. */
  offset: number
  /** Peak displacement of the wave, in px. */
  amplitude: number
  /** Desired distance between crests; rounded so the waves close seamlessly. */
  wavelength: number
  /** Phase in radians; animate it to make the waves travel. */
  phase: number
  /** Distance between sampled points, in px. */
  step?: number
}

interface Segment {
  length: number
  /** Point and outward normal at distance `s` along the segment. */
  at: (s: number) => { x: number; y: number; nx: number; ny: number }
}

/**
 * An SVG path that follows a rounded rectangle while undulating like a sine wave
 * perpendicular to its edge. The wave count is an integer, so the path closes seamlessly.
 */
export function wavyRoundedRectPath({
  width,
  height,
  radius,
  offset,
  amplitude,
  wavelength,
  phase,
  step = 4,
}: WavePathOptions): string {
  const left = -offset
  const top = -offset
  const right = width + offset
  const bottom = height + offset
  const r = Math.max(0, Math.min(radius + offset, (right - left) / 2, (bottom - top) / 2))

  const segments = roundedRectSegments(left, top, right, bottom, r)
  const perimeter = segments.reduce((total, segment) => total + segment.length, 0)
  if (perimeter <= 0) return ""

  const waves = Math.max(1, Math.round(perimeter / wavelength))
  const commands: string[] = []
  let travelled = 0

  for (const segment of segments) {
    for (let s = 0; s < segment.length; s += step) {
      const { x, y, nx, ny } = segment.at(s)
      const displacement = amplitude * Math.sin((2 * Math.PI * waves * (travelled + s)) / perimeter + phase)
      commands.push(`${commands.length ? "L" : "M"}${(x + nx * displacement).toFixed(2)} ${(y + ny * displacement).toFixed(2)}`)
    }
    travelled += segment.length
  }

  return `${commands.join("")}Z`
}

function roundedRectSegments(left: number, top: number, right: number, bottom: number, r: number): Segment[] {
  const straightX = right - left - 2 * r
  const straightY = bottom - top - 2 * r
  const arc = (Math.PI / 2) * r

  const corner = (cx: number, cy: number, startAngle: number): Segment => ({
    length: arc,
    at: (s) => {
      const angle = startAngle + (r > 0 ? s / r : 0)
      const nx = Math.cos(angle)
      const ny = Math.sin(angle)
      return { x: cx + r * nx, y: cy + r * ny, nx, ny }
    },
  })

  // Clockwise from the top-left, starting where the top edge leaves the corner.
  const segments: Segment[] = [
    { length: straightX, at: (s) => ({ x: left + r + s, y: top, nx: 0, ny: -1 }) },
    corner(right - r, top + r, -Math.PI / 2),
    { length: straightY, at: (s) => ({ x: right, y: top + r + s, nx: 1, ny: 0 }) },
    corner(right - r, bottom - r, 0),
    { length: straightX, at: (s) => ({ x: right - r - s, y: bottom, nx: 0, ny: 1 }) },
    corner(left + r, bottom - r, Math.PI / 2),
    { length: straightY, at: (s) => ({ x: left, y: bottom - r - s, nx: -1, ny: 0 }) },
    corner(left + r, top + r, Math.PI),
  ]
  return segments.filter((segment) => segment.length > 0)
}

/**
 * A horizontal sine wave spanning `width + wavelength`, centred vertically in `height`.
 * The extra wavelength lets the path be translated by one period for a seamless loop.
 */
export function sineWavePath(width: number, height: number, wavelength: number, amplitude: number, step = 2): string {
  const mid = height / 2
  const commands: string[] = []
  for (let x = 0; x <= width + wavelength; x += step) {
    const y = mid + amplitude * Math.sin((2 * Math.PI * x) / wavelength)
    commands.push(`${commands.length ? "L" : "M"}${x} ${y.toFixed(2)}`)
  }
  return commands.join("")
}

/**
 * A wave whose amplitude decays to a flat line, like a monitor trace that stops.
 * The wave occupies the first `activeFraction` of the width; the rest is flat.
 */
export function flatlinePath(
  width: number,
  height: number,
  wavelength: number,
  amplitude: number,
  activeFraction = 0.55,
  step = 2,
): string {
  const mid = height / 2
  const activeWidth = width * activeFraction
  const commands: string[] = []
  for (let x = 0; x <= width; x += step) {
    const envelope = Math.max(0, 1 - x / activeWidth) ** 1.4
    const y = mid + amplitude * envelope * Math.sin((2 * Math.PI * x) / wavelength)
    commands.push(`${commands.length ? "L" : "M"}${x} ${y.toFixed(2)}`)
  }
  return commands.join("")
}
