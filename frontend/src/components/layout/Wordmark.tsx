import { Link } from "react-router"

import { cn } from "@/lib/utils"

export function Wordmark({ className }: { className?: string }) {
  return (
    <Link
      to="/"
      aria-label="Package Health home"
      className={cn(
        "glass flex h-11 items-center rounded-full px-4 font-mono text-sm font-semibold tracking-tight text-foreground/85 transition-colors hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none",
        className,
      )}
    >
      pkg<span className="text-brand-blue">/</span>health
    </Link>
  )
}
