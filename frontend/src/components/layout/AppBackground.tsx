import type { CSSProperties } from "react"

interface Blob {
  className: string
  style: CSSProperties
}

// Large blurred color fields that drift slowly behind the glass surfaces.
const BLOBS: Blob[] = [
  {
    className: "-top-[20%] -left-[10%] size-[60vmax] bg-brand-blue/30 dark:bg-brand-blue/25",
    style: { "--drift-x": "8vw", "--drift-y": "6vh", "--drift-duration": "32s" } as CSSProperties,
  },
  {
    className: "top-[10%] -right-[15%] size-[55vmax] bg-brand-cyan/35 dark:bg-brand-cyan/20",
    style: { "--drift-x": "-7vw", "--drift-y": "8vh", "--drift-duration": "38s" } as CSSProperties,
  },
  {
    className: "-bottom-[25%] left-[20%] size-[50vmax] bg-sky-300/30 dark:bg-indigo-500/20",
    style: { "--drift-x": "5vw", "--drift-y": "-6vh", "--drift-duration": "44s" } as CSSProperties,
  },
]

export function AppBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-white via-sky-50 to-cyan-50 dark:from-slate-950 dark:via-[oklch(0.18_0.04_260)] dark:to-[oklch(0.2_0.05_230)]" />
      {BLOBS.map((blob) => (
        <div
          key={blob.className}
          className={`animate-drift absolute rounded-full blur-3xl ${blob.className}`}
          style={blob.style}
        />
      ))}
      <div className="absolute inset-0 bg-white/25 dark:bg-transparent" />
    </div>
  )
}
