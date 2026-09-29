import { Fragment } from "react"

import { Select, SelectContent, SelectItem, SelectSeparator, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AUTO_ECOSYSTEM, ECOSYSTEM_CHOICES } from "@/lib/ecosystems"
import { cn } from "@/lib/utils"
import type { EcosystemChoice } from "@/types/analysis"

interface EcosystemSelectProps {
  value: EcosystemChoice
  onChange: (ecosystem: EcosystemChoice) => void
  disabled?: boolean
  className?: string
}

export function EcosystemSelect({ value, onChange, disabled, className }: EcosystemSelectProps) {
  return (
    <Select value={value} onValueChange={(next) => onChange(next as EcosystemChoice)} disabled={disabled}>
      <SelectTrigger aria-label="Package ecosystem" className={cn("glass-inset h-12! rounded-xl", className)}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {ECOSYSTEM_CHOICES.map((choice) => (
          <Fragment key={choice.id}>
            <SelectItem value={choice.id}>
              <span className="font-medium">{choice.label}</span>
              <span className="text-xs text-muted-foreground in-data-[slot=select-trigger]:hidden">{choice.language}</span>
            </SelectItem>
            {choice.id === AUTO_ECOSYSTEM.id && <SelectSeparator />}
          </Fragment>
        ))}
      </SelectContent>
    </Select>
  )
}
