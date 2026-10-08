import { PencilLine, RotateCw } from "lucide-react"

import { Flatline } from "@/components/effects/Flatline"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import type { AnalysisFailure, FailureKind } from "@/types/analysis"

interface FailureCopy {
  title: string
  description: string
  /** Offer a retry: pointless when the input itself is wrong. */
  retryable: boolean
  /** Show the server's message verbatim (it carries the specific reason). */
  showMessage: boolean
  /** Show the request ID, so a report of the problem can be matched to the server's logs and traces. */
  showReference: boolean
  hint?: string
}

const FAILURE_COPY: Record<FailureKind, FailureCopy> = {
  unreachable: {
    title: "Can't reach the analysis server",
    description: "The backend isn't responding. Make sure it's running, then try again.",
    retryable: true,
    showMessage: false,
    showReference: false,
    hint: "cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000",
  },
  invalid: {
    title: "That input doesn't look right",
    description: "Adjust the package name or dependency file and run it again.",
    retryable: false,
    showMessage: true,
    showReference: false,
  },
  limited: {
    title: "Give it a moment",
    description: "There's a limit on how many checks can run, which keeps the site free for everyone.",
    retryable: true,
    showMessage: true,
    showReference: false,
  },
  server: {
    title: "The analysis hit a snag",
    description: "Something went wrong while checking the packages. It's usually temporary.",
    retryable: true,
    showMessage: true,
    showReference: true,
  },
}

interface ErrorStateProps {
  failure: AnalysisFailure
  onRetry?: () => void
  /** Omitted when the search panel is already on screen. */
  onEdit?: () => void
}

export function ErrorState({ failure, onRetry, onEdit }: ErrorStateProps) {
  const copy = FAILURE_COPY[failure.kind]
  const canRetry = copy.retryable && onRetry

  return (
    <Card role="alert" className="animate-in fade-in-0 zoom-in-[0.98] duration-300">
      <CardContent className="flex flex-col items-center px-6 py-6 text-center sm:px-10">
        <Flatline className="h-14 w-full max-w-xs" />

        <h2 className="mt-6 text-lg font-semibold">{copy.title}</h2>
        <p className="mt-1.5 max-w-md text-sm text-balance text-muted-foreground">{copy.description}</p>

        {copy.showMessage && failure.message && (
          <p className="glass-inset mt-4 max-w-md rounded-xl px-3.5 py-2 text-sm">{failure.message}</p>
        )}
        {copy.showReference && failure.requestId && (
          <p className="mt-3 text-xs text-muted-foreground">
            Reference <span className="font-mono text-foreground/80 select-all">{failure.requestId}</span>
          </p>
        )}
        {copy.hint && (
          <code className="glass-inset mt-4 max-w-full overflow-x-auto rounded-xl px-3.5 py-2 font-mono text-xs whitespace-nowrap">
            {copy.hint}
          </code>
        )}

        {(canRetry || onEdit) && (
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {canRetry && (
              <Button
                onClick={onRetry}
                className="h-10 rounded-xl bg-gradient-to-r from-brand-blue to-brand-cyan px-4 text-white shadow-lg shadow-brand-blue/25 hover:brightness-110"
              >
                <RotateCw /> Try again
              </Button>
            )}
            {onEdit && (
              <Button
                variant="ghost"
                onClick={onEdit}
                className={
                  canRetry
                    ? "glass-inset h-10 rounded-xl px-4"
                    : "h-10 rounded-xl bg-gradient-to-r from-brand-blue to-brand-cyan px-4 text-white shadow-lg shadow-brand-blue/25 hover:brightness-110"
                }
              >
                <PencilLine /> Edit search
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
