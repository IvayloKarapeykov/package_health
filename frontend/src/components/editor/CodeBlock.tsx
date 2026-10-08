import { Check, Copy, FileCode2, SquareTerminal } from "lucide-react"
import { lazy, Suspense, useState } from "react"

import type { CodeViewProps } from "@/components/editor/CodeView"
import { cn } from "@/lib/utils"

const CodeView = lazy(() => import("@/components/editor/CodeView"))

interface CodeBlockProps extends CodeViewProps {
  /** Shown in the tab: a file name, or what the snippet is for. */
  title: string
  className?: string
}

export function CodeBlock({ title, code, language, lineNumbers, className }: CodeBlockProps) {
  const Icon = language === "shell" ? SquareTerminal : FileCode2
  return (
    <div className={cn("glass-inset overflow-hidden rounded-xl", className)}>
      <div className="flex h-9 items-center gap-2 border-b border-border/60 pr-1.5 pl-3 text-xs">
        <Icon className="size-3.5 shrink-0 text-brand-blue" aria-hidden />
        <span className="truncate font-mono text-foreground/85">{title}</span>
        <CopyButton text={code} className="ml-auto" />
      </div>
      <Suspense fallback={<pre className="overflow-x-auto px-3.5 py-3 font-mono text-xs leading-[1.65]">{code}</pre>}>
        <CodeView code={code} language={language} lineNumbers={lineNumbers} />
      </Suspense>
    </div>
  )
}

function CopyButton({ text, className }: { text: string; className?: string }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const Icon = copied ? Check : Copy
  return (
    <button
      type="button"
      onClick={copy}
      aria-label={copied ? "Copied" : "Copy to clipboard"}
      className={cn(
        "grid size-7 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none",
        copied && "text-success hover:text-success",
        className,
      )}
    >
      <Icon className="size-3.5" />
    </button>
  )
}
