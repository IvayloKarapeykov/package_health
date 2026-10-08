import { readJson, remove, writeJson, type WriteResult } from "@/lib/storage"

export interface ApiKeys {
  githubToken: string
  openRouterKey: string
}

const STORAGE_KEY = "package-health:keys"
const NO_KEYS: ApiKeys = { githubToken: "", openRouterKey: "" }

let current: ApiKeys = readJson<ApiKeys>(STORAGE_KEY) ?? NO_KEYS
const listeners = new Set<() => void>()

export function getKeys(): ApiKeys {
  return current
}

export function hasKeys(keys: ApiKeys): boolean {
  return Boolean(keys.githubToken || keys.openRouterKey)
}

export function saveKeys(keys: ApiKeys): WriteResult {
  const next = { githubToken: keys.githubToken.trim(), openRouterKey: keys.openRouterKey.trim() }
  if (!hasKeys(next)) {
    clearKeys()
    return "ok"
  }
  const result = writeJson(STORAGE_KEY, next)
  if (result === "ok") update(next)
  return result
}

export function clearKeys(): void {
  remove(STORAGE_KEY)
  update(NO_KEYS)
}

export function subscribeKeys(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

/** The headers the API reads a caller's own keys from. */
export function keyHeaders(keys: ApiKeys = current): Record<string, string> {
  const headers: Record<string, string> = {}
  if (keys.githubToken) headers["X-GitHub-Token"] = keys.githubToken
  if (keys.openRouterKey) headers["X-OpenRouter-Key"] = keys.openRouterKey
  return headers
}

function update(keys: ApiKeys) {
  current = keys
  for (const listener of listeners) listener()
}
