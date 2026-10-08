import { useSyncExternalStore } from "react"

import { getKeys, subscribeKeys } from "@/lib/keys"

export function useKeys() {
  return useSyncExternalStore(subscribeKeys, getKeys)
}
