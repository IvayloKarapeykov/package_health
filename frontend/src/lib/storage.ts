/**
 * Safe wrappers over localStorage. Storage can be unavailable (private mode, blocked site data)
 * or full, so reads fall back to `null` and writes report whether they succeeded.
 */

export function readString(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function readJson<T>(key: string): T | null {
  const raw = readString(key)
  if (raw === null) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

export type WriteResult = "ok" | "quota" | "unavailable"

export function writeString(key: string, value: string): WriteResult {
  try {
    localStorage.setItem(key, value)
    return "ok"
  } catch (error) {
    return isQuotaError(error) ? "quota" : "unavailable"
  }
}

export function writeJson(key: string, value: unknown): WriteResult {
  return writeString(key, JSON.stringify(value))
}

export function remove(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch {
    // storage unavailable: nothing to remove
  }
}

function isQuotaError(error: unknown): boolean {
  return (
    error instanceof DOMException &&
    (error.name === "QuotaExceededError" || error.name === "NS_ERROR_DOM_QUOTA_REACHED")
  )
}
