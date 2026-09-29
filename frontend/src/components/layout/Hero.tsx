import { cn } from "@/lib/utils"

interface HeroProps {
  /** Collapses the headline once results are on screen. */
  compact: boolean
}

export function Hero({ compact }: HeroProps) {
  return (
    <section
      className={cn(
        "grid text-center transition-[grid-template-rows,opacity] duration-500 ease-out",
        compact ? "grid-rows-[0fr] opacity-0" : "grid-rows-[1fr] opacity-100",
      )}
    >
      <div className="overflow-hidden">
        <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          Should I use this <span className="text-gradient-brand">library</span>?
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-balance text-muted-foreground">
          Downloads, release history, GitHub activity and known vulnerabilities, turned into a verdict with reasons
          and better alternatives. For npm, PyPI, Maven, NuGet, Go, crates.io, RubyGems and Packagist.
        </p>
      </div>
    </section>
  )
}
