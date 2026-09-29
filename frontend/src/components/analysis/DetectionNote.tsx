import { Button } from "@/components/ui/button"
import { ECOSYSTEM_BY_ID } from "@/lib/ecosystems"
import type { Ecosystem, EcosystemDetection } from "@/types/analysis"

interface DetectionNoteProps {
  detection: EcosystemDetection
  /** Re-run the same package in another registry that also publishes the name. */
  onSwitch?: (ecosystem: Ecosystem) => void
}

/** Says which registry "auto" picked, and offers the other registries that publish the same name. */
export function DetectionNote({ detection, onSwitch }: DetectionNoteProps) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 pl-1 text-xs text-muted-foreground">
      <span>
        Detected on <span className="font-medium text-foreground">{ECOSYSTEM_BY_ID[detection.ecosystem].label}</span>
        {detection.alsoFoundIn.length > 0 ? ", where it's most used · also on" : ""}
      </span>
      {detection.alsoFoundIn.map((ecosystem) => (
        <Button
          key={ecosystem}
          type="button"
          variant="ghost"
          size="xs"
          className="glass-inset rounded-full px-2.5 hover:border-brand-cyan/60"
          disabled={!onSwitch}
          onClick={() => onSwitch?.(ecosystem)}
          title={`Analyze the ${ECOSYSTEM_BY_ID[ecosystem].label} package instead`}
        >
          {ECOSYSTEM_BY_ID[ecosystem].label}
        </Button>
      ))}
    </div>
  )
}
