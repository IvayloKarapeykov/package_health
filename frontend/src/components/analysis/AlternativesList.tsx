import { ArrowRight, Download } from "lucide-react"

import { describeAdoption } from "@/lib/format"
import type { Alternative } from "@/types/analysis"

export function AlternativesList({ alternatives }: { alternatives: Alternative[] }) {
  if (!alternatives.length) return null
  return (
    <section>
      <h4 className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">Consider instead</h4>
      <ul className="grid gap-2 sm:grid-cols-3">
        {alternatives.map((alternative) => {
          const adoption = describeAdoption(alternative.adoption)
          return (
            <li key={alternative.name}>
              <a
                href={alternative.url ?? undefined}
                target="_blank"
                rel="noreferrer"
                className="group glass-inset flex h-full flex-col gap-1 rounded-xl p-3 transition hover:-translate-y-0.5 hover:border-brand-cyan/60"
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="truncate font-mono text-sm font-medium" title={alternative.name}>
                    {alternative.name}
                  </span>
                  <ArrowRight className="size-3.5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
                </span>
                <span className="text-xs text-muted-foreground">{alternative.reason}</span>
                {adoption.value !== "—" && (
                  <span className="mt-auto flex items-center gap-1 pt-1 font-mono text-xs text-muted-foreground" title={adoption.hint}>
                    <Download className="size-3" aria-hidden />
                    {adoption.value} {adoption.label.toLowerCase()}
                  </span>
                )}
              </a>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
