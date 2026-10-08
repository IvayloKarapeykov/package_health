import { ScanSearch } from "lucide-react"
import { NavLink } from "react-router"

import { GitHubIcon } from "@/components/icons/GitHubIcon"
import { GITHUB_URL } from "@/lib/links"
import { cn } from "@/lib/utils"

const ITEM =
  "flex h-8 items-center gap-1.5 rounded-full border border-transparent px-3 text-sm font-medium text-foreground/70 transition-colors hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"

export function SiteNav({ className }: { className?: string }) {
  return (
    <nav aria-label="Main" className={cn("glass flex h-11 items-center gap-0.5 rounded-full px-1.5", className)}>
      <NavLink to="/app" className={({ isActive }) => cn(ITEM, isActive && "bg-background text-foreground shadow-sm dark:border-input dark:bg-input/30")}>
        <ScanSearch className="size-4" aria-hidden />
        <span className="max-sm:sr-only">Analyze</span>
      </NavLink>
      <a href={GITHUB_URL} target="_blank" rel="noreferrer" className={ITEM}>
        <GitHubIcon className="size-4" />
        <span className="max-sm:sr-only">GitHub</span>
      </a>
    </nav>
  )
}
