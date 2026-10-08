import { ArrowDown, ArrowRight } from "lucide-react"
import { Link } from "react-router"

import { ECOSYSTEMS } from "@/lib/ecosystems"

export function LandingHero({ onShowExample }: { onShowExample: () => void }) {
  return (
    <section className="mx-auto max-w-4xl px-4 pt-[18svh] pb-8 text-center">
      <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
        Should I use this <span className="text-gradient-brand">library</span>?
      </h1>
      <p className="mx-auto mt-5 max-w-xl text-lg text-balance text-muted-foreground">
        Adoption, maintenance and known vulnerabilities for any package, turned into a clear verdict with the reasons
        and better alternatives.
      </p>
      <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
        <Link
          to="/app"
          className="flex h-11 items-center gap-2 rounded-full bg-gradient-to-r from-brand-blue to-brand-cyan px-5 text-sm font-medium text-white shadow-lg shadow-brand-blue/25 transition hover:brightness-110 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          Check a package
          <ArrowRight className="size-4" aria-hidden />
        </Link>
        <button
          type="button"
          onClick={onShowExample}
          className="glass flex h-11 items-center gap-2 rounded-full px-5 text-sm font-medium text-foreground/85 transition hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          See a real report
          <ArrowDown className="size-4" aria-hidden />
        </button>
      </div>
      <p className="mt-5 text-sm text-muted-foreground">Free and open source · No account needed</p>
      <ul className="mx-auto mt-14 flex max-w-2xl flex-wrap justify-center gap-x-5 gap-y-2 text-sm text-muted-foreground">
        {ECOSYSTEMS.map((ecosystem) => (
          <li key={ecosystem.id} title={ecosystem.language}>
            {ecosystem.label}
          </li>
        ))}
      </ul>
    </section>
  )
}
