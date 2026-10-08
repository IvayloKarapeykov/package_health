import { cn } from "@/lib/utils"

interface WordmarkProps {
  onClick: () => void
  className?: string
}

export function Wordmark({ onClick, className }: WordmarkProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Package Health Advisor — start over"
      className={cn(
        "font-mono text-sm font-semibold tracking-tight text-foreground/85 transition-colors hover:text-foreground",
        className,
      )}
    >
      pkg<span className="text-brand-blue">/</span>health
    </button>
  )
}
