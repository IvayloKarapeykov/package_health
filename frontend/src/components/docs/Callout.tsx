import { Info, Lightbulb, TriangleAlert } from "lucide-react"
import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

const KINDS = {
  note: { icon: Info, className: "border-brand-blue/30 bg-brand-blue/5 [&>svg]:text-brand-blue" },
  tip: { icon: Lightbulb, className: "border-success/30 bg-success/5 [&>svg]:text-success" },
  warning: { icon: TriangleAlert, className: "border-warning/40 bg-warning/10 [&>svg]:text-warning-foreground" },
}

function Callout({ kind, children }: { kind: keyof typeof KINDS; children: ReactNode }) {
  const { icon: Icon, className } = KINDS[kind]
  return (
    <div className={cn("mt-6 flex gap-3 rounded-xl border px-4 py-3 text-sm leading-6 [&_p]:mt-0", className)}>
      <Icon className="mt-1 size-4 shrink-0" aria-hidden />
      <div className="min-w-0">{children}</div>
    </div>
  )
}

export const Note = ({ children }: { children: ReactNode }) => <Callout kind="note">{children}</Callout>
export const Tip = ({ children }: { children: ReactNode }) => <Callout kind="tip">{children}</Callout>
export const Warning = ({ children }: { children: ReactNode }) => <Callout kind="warning">{children}</Callout>
