import type { Adoption } from "@/types/analysis"

const compactNumber = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 })
const relativeTime = new Intl.RelativeTimeFormat("en", { numeric: "auto" })
const fullDate = new Intl.DateTimeFormat("en", { dateStyle: "medium" })

const DAY_MS = 24 * 60 * 60 * 1000

export function formatCompact(value: number | null | undefined): string {
  return value == null ? "—" : compactNumber.format(value)
}

export function formatRelativeDate(iso: string | null | undefined): string {
  if (!iso) return "—"
  const days = Math.round((new Date(iso).getTime() - Date.now()) / DAY_MS)
  const abs = Math.abs(days)
  if (abs < 1) return "today"
  if (abs < 30) return relativeTime.format(days, "day")
  if (abs < 365) return relativeTime.format(Math.round(days / 30), "month")
  return relativeTime.format(Math.round(days / 365), "year")
}

/** "just now", "5 minutes ago", "yesterday"… for timestamps in the recent past. */
export function formatTimeAgo(timestamp: number): string {
  const seconds = Math.round((timestamp - Date.now()) / 1000)
  const abs = Math.abs(seconds)
  if (abs < 60) return "just now"
  if (abs < 3600) return relativeTime.format(Math.round(seconds / 60), "minute")
  if (abs < 86400) return relativeTime.format(Math.round(seconds / 3600), "hour")
  return relativeTime.format(Math.round(seconds / 86400), "day")
}

export function formatDate(iso: string | null | undefined): string {
  return iso ? fullDate.format(new Date(iso)) : "—"
}

export function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null) return "—"
  const units = ["B", "kB", "MB", "GB"]
  let value = bytes
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit += 1
  }
  return `${value.toFixed(value < 10 && unit > 0 ? 1 : 0)} ${units[unit]}`
}

export interface AdoptionFigure {
  label: string
  value: string
  hint?: string
}

/** The most informative adoption measure the registry offers: recent downloads, then all-time, then dependents. */
export function describeAdoption(adoption: Adoption | null | undefined): AdoptionFigure {
  const hint = adoption?.note ?? undefined
  if (adoption?.weeklyDownloads != null) {
    return { label: "Weekly downloads", value: formatCompact(adoption.weeklyDownloads), hint }
  }
  if (adoption?.totalDownloads != null) {
    return { label: "Total downloads", value: formatCompact(adoption.totalDownloads), hint }
  }
  if (adoption?.dependents != null) {
    return { label: "Dependents", value: formatCompact(adoption.dependents), hint }
  }
  return { label: "Downloads", value: "—", hint: hint ?? "Not published by this registry" }
}
