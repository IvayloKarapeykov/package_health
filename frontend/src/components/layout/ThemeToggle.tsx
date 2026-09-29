import { Moon, Sun } from "lucide-react"

import type { Theme } from "@/hooks/useTheme"
import { cn } from "@/lib/utils"

interface ThemeToggleProps {
  theme: Theme
  onToggle: () => void
  className?: string
}

/** A floating glass button that switches between light and dark mode. */
export function ThemeToggle({ theme, onToggle, className }: ThemeToggleProps) {
  const Icon = theme === "dark" ? Sun : Moon
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      className={cn(
        "glass grid size-11 place-items-center rounded-full text-foreground/80 transition hover:scale-105 hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none",
        className,
      )}
    >
      <Icon className="size-[18px]" />
    </button>
  )
}
