import { ArrowRight } from "lucide-react"
import { Link } from "react-router"

import { GitHubIcon } from "@/components/icons/GitHubIcon"
import { GITHUB_URL } from "@/lib/links"

export default function LandingPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 pt-[22svh] pb-20 text-center">
      <title>Package Health · Should I use this library?</title>
      <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
        Should I use this <span className="text-gradient-brand">library</span>?
      </h1>
      <p className="mx-auto mt-5 max-w-xl text-lg text-balance text-muted-foreground">
        Adoption, maintenance and known vulnerabilities for any package, turned into a clear verdict with reasons and
        alternatives. Free and open source.
      </p>
      <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
        <Link
          to="/app"
          className="flex h-11 items-center gap-2 rounded-full bg-gradient-to-r from-brand-blue to-brand-cyan px-5 text-sm font-medium text-white shadow-lg shadow-brand-blue/25 transition hover:brightness-110 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          Check a package
          <ArrowRight className="size-4" aria-hidden />
        </Link>
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noreferrer"
          className="glass flex h-11 items-center gap-2 rounded-full px-5 text-sm font-medium text-foreground/85 transition hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          <GitHubIcon className="size-4" />
          View on GitHub
        </a>
      </div>
    </main>
  )
}
