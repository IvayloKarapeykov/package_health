import { readServerSentEvents, StreamIdleError } from "@/api/sse"
import { keyHeaders } from "@/lib/keys"
import type { AnalysisEvent, AnalysisRequest, FailureKind } from "@/types/analysis"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""

export class ApiError extends Error {
  readonly kind: FailureKind
  readonly requestId: string | null

  constructor(kind: FailureKind, message: string, requestId: string | null = null) {
    super(message)
    this.kind = kind
    this.requestId = requestId
  }
}

const REQUEST_ID_HEADER = "X-Request-ID"

// The backend pings every 5 s; this much silence means the connection is dead
// (a proxy may keep it open after the backend has gone away).
const STREAM_IDLE_TIMEOUT_MS = 15_000

// A dev proxy or gateway answers with these when the backend itself is down.
const UNREACHABLE_STATUSES = new Set([502, 503, 504])

export async function* streamAnalysis(
  request: AnalysisRequest,
  signal?: AbortSignal,
): AsyncGenerator<AnalysisEvent> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api/analyze/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream", ...keyHeaders() },
      body: JSON.stringify(request),
      signal,
    })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new ApiError("unreachable", "Could not reach the analysis server.")
  }

  const requestId = response.headers.get(REQUEST_ID_HEADER)
  if (!response.ok || !response.body) {
    throw new ApiError(classifyStatus(response.status), await describeFailure(response), requestId)
  }

  try {
    for await (const { data } of readServerSentEvents(response.body, { idleTimeoutMs: STREAM_IDLE_TIMEOUT_MS })) {
      yield JSON.parse(data) as AnalysisEvent
    }
  } catch (error) {
    if (error instanceof StreamIdleError) {
      throw new ApiError("unreachable", "Lost connection to the analysis server.", requestId)
    }
    throw error
  }
}

function classifyStatus(status: number): FailureKind {
  if (UNREACHABLE_STATUSES.has(status)) return "unreachable"
  if (status === 400 || status === 422) return "invalid"
  if (status === 429) return "limited"
  return "server"
}

async function describeFailure(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === "string") return body.detail
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg
  } catch {
    // fall through to the generic message
  }
  return `The server responded with ${response.status}.`
}
