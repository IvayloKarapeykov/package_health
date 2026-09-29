import { useCallback, useEffect, useLayoutEffect, useReducer, useRef } from "react"

import { ApiError, streamAnalysis } from "@/api/analysis"
import type { SavedSearch } from "@/lib/searchHistory"
import type {
  AnalysisEvent,
  AnalysisFailure,
  AnalysisReport,
  AnalysisRequest,
  AssessmentStep,
  DependencyRef,
  EcosystemDetection,
  PackageAssessment,
  SkippedDependency,
} from "@/types/analysis"
import { dependencyKey } from "@/types/analysis"

export type AnalysisStatus = "idle" | "running" | "done" | "error"

export interface AnalysisState {
  status: AnalysisStatus
  /** The detected dependency file format (e.g. "pyproject.toml"); null for a single package. */
  manifest: string | null
  /** How an "auto" package was resolved; null otherwise. */
  detection: EcosystemDetection | null
  planned: DependencyRef[]
  skipped: SkippedDependency[]
  /** The step each in-flight package is currently on, keyed by `dependencyKey`. */
  progress: Record<string, AssessmentStep>
  /** Finished assessments, keyed by `dependencyKey`. */
  assessments: Record<string, PackageAssessment>
  report: AnalysisReport | null
  error: AnalysisFailure | null
  /** When the shown report was saved, if it was reopened from history rather than just run. */
  savedAt: number | null
}

type Action =
  | { type: "start" }
  | { type: "event"; event: AnalysisEvent }
  | { type: "fail"; failure: AnalysisFailure }
  | { type: "reset" }
  | { type: "restore"; saved: SavedSearch }

const initialState: AnalysisState = {
  status: "idle",
  manifest: null,
  detection: null,
  planned: [],
  skipped: [],
  progress: {},
  assessments: {},
  report: null,
  error: null,
  savedAt: null,
}

function reducer(state: AnalysisState, action: Action): AnalysisState {
  switch (action.type) {
    case "start":
      return { ...initialState, status: "running" }
    case "reset":
      return initialState
    case "fail":
      return { ...state, status: "error", error: action.failure }
    case "event":
      return applyEvent(state, action.event)
    case "restore":
      return restore(action.saved)
  }
}

function applyEvent(state: AnalysisState, event: AnalysisEvent): AnalysisState {
  switch (event.type) {
    case "plan":
      return {
        ...state,
        manifest: event.manifest,
        detection: event.detection,
        planned: event.dependencies,
        skipped: event.skipped,
      }
    case "progress":
      return { ...state, progress: { ...state.progress, [event.dependencyKey]: event.step } }
    case "assessment":
      return {
        ...state,
        assessments: { ...state.assessments, [dependencyKey(event.assessment.dependency)]: event.assessment },
      }
    case "report":
      return { ...state, status: "done", report: event.report }
    case "error":
      return {
        ...state,
        status: "error",
        error: {
          kind: event.kind === "invalid_input" ? "invalid" : "server",
          message: event.message,
          requestId: event.requestId,
        },
      }
  }
}

/** A finished analysis from history, in the same shape a live run ends in. */
function restore({ report, detection, savedAt }: SavedSearch): AnalysisState {
  return {
    ...initialState,
    status: "done",
    manifest: report.manifest,
    detection,
    planned: report.assessments.map((assessment) => assessment.dependency),
    skipped: report.skipped,
    assessments: Object.fromEntries(report.assessments.map((a) => [dependencyKey(a.dependency), a])),
    report,
    savedAt,
  }
}

function toFailure(error: unknown): AnalysisFailure {
  if (error instanceof ApiError) return { kind: error.kind, message: error.message, requestId: error.requestId }
  return { kind: "server", message: error instanceof Error ? error.message : String(error) }
}

interface UseAnalysisOptions {
  /** Called once a run finishes with a report, e.g. to save it to history. */
  onReport?: (request: AnalysisRequest, report: AnalysisReport, detection: EcosystemDetection | null) => void
}

export function useAnalysis({ onReport }: UseAnalysisOptions = {}) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const controllerRef = useRef<AbortController | null>(null)
  const onReportRef = useRef(onReport)
  useLayoutEffect(() => {
    onReportRef.current = onReport
  })

  const cancel = useCallback(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
  }, [])

  const analyze = useCallback(
    async (request: AnalysisRequest) => {
      cancel()
      const controller = new AbortController()
      controllerRef.current = controller
      dispatch({ type: "start" })

      let finished = false
      let detection: EcosystemDetection | null = null
      try {
        for await (const event of streamAnalysis(request, controller.signal)) {
          finished ||= event.type === "report" || event.type === "error"
          dispatch({ type: "event", event })
          if (event.type === "plan") detection = event.detection
          if (event.type === "report") onReportRef.current?.(request, event.report, detection)
        }
        if (!finished && !controller.signal.aborted) {
          dispatch({
            type: "fail",
            failure: { kind: "server", message: "The connection closed before the analysis finished." },
          })
        }
      } catch (error) {
        if (controller.signal.aborted) return
        dispatch({ type: "fail", failure: toFailure(error) })
      }
    },
    [cancel],
  )

  const restoreSaved = useCallback(
    (saved: SavedSearch) => {
      cancel()
      dispatch({ type: "restore", saved })
    },
    [cancel],
  )

  const reset = useCallback(() => {
    cancel()
    dispatch({ type: "reset" })
  }, [cancel])

  useEffect(() => cancel, [cancel])

  return { state, analyze, restore: restoreSaved, reset }
}
