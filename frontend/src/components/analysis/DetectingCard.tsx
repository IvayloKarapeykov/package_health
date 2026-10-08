import { WaveLine } from "@/components/effects/WaveLine"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { ECOSYSTEMS } from "@/lib/ecosystems"

export function DetectingCard({ spec }: { spec: string }) {
  return (
    <Card aria-busy>
      <CardHeader className="flex items-start justify-between gap-4">
        <span className="truncate font-mono text-base font-semibold" title={spec}>
          {spec}
        </span>
        <span className="shrink-0 font-mono text-xs text-muted-foreground">detecting</span>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground" aria-live="polite">
          Finding the registry that publishes it…
        </p>
        <WaveLine gradient flowing className="h-6 w-full" wavelength={80} amplitude={6} strokeWidth={2} duration="1.4s" />
        <div className="flex flex-wrap gap-1.5">
          {ECOSYSTEMS.map((ecosystem, index) => (
            <span
              key={ecosystem.id}
              className="glass-inset animate-pulse rounded-full px-2 py-px text-[10px] font-medium text-muted-foreground"
              style={{ animationDelay: `${index * 120}ms` }}
            >
              {ecosystem.label}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
