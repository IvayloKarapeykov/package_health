import { BookOpen, Coffee, ScanSearch } from "lucide-react"
import { Link } from "react-router"

import { GitHubIcon } from "@/components/icons/GitHubIcon"
import { COFFEE_URL, GITHUB_URL } from "@/lib/links"

const LINK = "inline-flex items-center gap-1.5 transition-colors hover:text-foreground"

export function SiteFooter() {
  return (
    <footer className="mx-auto max-w-6xl px-4 pt-10 pb-12">
      <div className="flex flex-col gap-6 border-t border-border pt-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <p>Free and open source under the MIT license.</p>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-5 gap-y-2">
          <Link to="/app" className={LINK}>
            <ScanSearch className="size-4" aria-hidden />
            Analyze
          </Link>
          <Link to="/docs" className={LINK}>
            <BookOpen className="size-4" aria-hidden />
            Docs
          </Link>
          <a href={GITHUB_URL} target="_blank" rel="noreferrer" className={LINK}>
            <GitHubIcon className="size-4" />
            GitHub
          </a>
          <a href={COFFEE_URL} target="_blank" rel="noreferrer" className={LINK}>
            <Coffee className="size-4" aria-hidden />
            Buy me a coffee
          </a>
        </nav>
      </div>
    </footer>
  )
}
