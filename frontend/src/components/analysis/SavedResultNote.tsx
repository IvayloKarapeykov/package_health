import { RotateCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { formatTimeAgo } from "@/lib/format"

interface SavedResultNoteProps {
  savedAt: number
  onRerun?: () => void
}

/** Marks a report reopened from history, since registries and advisories may have changed since. */
export function SavedResultNote({ savedAt, onRerun }: SavedResultNoteProps) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 pl-1 text-xs text-muted-foreground">
      <span>Saved result from {formatTimeAgo(savedAt)}</span>
      {onRerun && (
        <Button
          type="button"
          variant="ghost"
          size="xs"
          className="glass-inset rounded-full px-2.5 hover:border-brand-cyan/60"
          onClick={onRerun}
        >
          <RotateCw aria-hidden /> Run again
        </Button>
      )}
    </div>
  )
}
