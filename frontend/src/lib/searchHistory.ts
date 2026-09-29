/**
 * Recent searches, persisted in localStorage.
 *
 * Two layers keep startup cheap:
 *  - a small index (label, verdict, time) that the recent list renders from, read once;
 *  - one entry per search holding the request and full report, read only when it is opened.
 * The oldest searches are evicted past MAX_SEARCHES, or when storage runs out of room.
 */

import { ECOSYSTEM_BY_ID } from "@/lib/ecosystems"
import { readJson, remove, writeJson } from "@/lib/storage"
import type { AnalysisReport, AnalysisRequest, Ecosystem, EcosystemDetection, Verdict } from "@/types/analysis"

const VERSION = 1
const INDEX_KEY = `package-health:history:v${VERSION}`
const entryKey = (id: string) => `${INDEX_KEY}:${id}`

export const MAX_SEARCHES = 12

/** What the recent list shows; small enough to read on every page load. */
export interface SearchSummary {
  id: string
  /** Package name, or the dependency file format. */
  label: string
  /** Registry, or the number of dependencies in a file. */
  detail: string
  ecosystem: Ecosystem
  verdict: Verdict
  savedAt: number
}

/** Everything needed to show a search again without re-running it. */
export interface SavedSearch {
  request: AnalysisRequest
  report: AnalysisReport
  detection: EcosystemDetection | null
  savedAt: number
}

// --- Index cache + subscriptions (the shape useSyncExternalStore expects) -----------------------

let index: SearchSummary[] | null = null
const listeners = new Set<() => void>()

export function getSearches(): SearchSummary[] {
  index ??= readIndex()
  return index
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  if (listeners.size === 1) window.addEventListener("storage", onStorage)
  return () => {
    listeners.delete(listener)
    if (listeners.size === 0) window.removeEventListener("storage", onStorage)
  }
}

/** Another tab changed the history: drop the cached index so the next read picks it up. */
function onStorage(event: StorageEvent) {
  if (event.key !== null && event.key !== INDEX_KEY) return
  index = null
  notify()
}

function setIndex(next: SearchSummary[]) {
  index = next
  writeJson(INDEX_KEY, next)
  notify()
}

function notify() {
  for (const listener of listeners) listener()
}

function readIndex(): SearchSummary[] {
  const stored = readJson<unknown>(INDEX_KEY)
  return Array.isArray(stored) ? (stored as SearchSummary[]) : []
}

// --- Reads and writes ------------------------------------------------------------------------------

export function saveSearch(request: AnalysisRequest, report: AnalysisReport, detection: EcosystemDetection | null) {
  const summary = summarize(request, report)
  const entry: SavedSearch = { request, report, detection, savedAt: summary.savedAt }

  // The same search moves to the top instead of being listed twice.
  const kept = getSearches().filter((search) => search.id !== summary.id)
  const evicted = kept.splice(MAX_SEARCHES - 1)

  // Out of room: drop the oldest searches until the new one fits (or none are left).
  while (writeJson(entryKey(summary.id), entry) === "quota") {
    const oldest = kept.pop()
    if (!oldest) return
    evicted.push(oldest)
    remove(entryKey(oldest.id))
  }
  for (const search of evicted) remove(entryKey(search.id))
  setIndex([summary, ...kept])
}

/** The full saved search, or null if its entry is gone (then it is dropped from the index too). */
export function loadSearch(id: string): SavedSearch | null {
  const entry = readJson<SavedSearch>(entryKey(id))
  if (!entry?.report) {
    removeSearch(id)
    return null
  }
  return entry
}

export function removeSearch(id: string) {
  remove(entryKey(id))
  setIndex(getSearches().filter((search) => search.id !== id))
}

export function clearSearches() {
  for (const search of getSearches()) remove(entryKey(search.id))
  setIndex([])
}

// --- Identity --------------------------------------------------------------------------------------

function summarize(request: AnalysisRequest, report: AnalysisReport): SearchSummary {
  const savedAt = Date.now()
  if (request.mode === "package") {
    // Keyed by what was analyzed, so "requests" on auto and on PyPI are the same search.
    const name = report.assessments[0]?.dependency.name ?? request.package.trim()
    return {
      id: `package:${report.ecosystem}:${name}`,
      label: name,
      detail: ECOSYSTEM_BY_ID[report.ecosystem].label,
      ecosystem: report.ecosystem,
      verdict: report.overallVerdict,
      savedAt,
    }
  }
  const count = report.assessments.length
  return {
    id: `manifest:${hash(request.content)}:${request.includeDev ? "dev" : "prod"}`,
    label: report.manifest ?? "dependency file",
    detail: `${count} dep${count === 1 ? "" : "s"}`,
    ecosystem: report.ecosystem,
    verdict: report.overallVerdict,
    savedAt,
  }
}

/** FNV-1a: a fast, stable fingerprint for a pasted file (not for security). */
function hash(text: string): string {
  let h = 0x811c9dc5
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i)
    h = Math.imul(h, 0x01000193)
  }
  return `${(h >>> 0).toString(36)}${text.length.toString(36)}`
}
