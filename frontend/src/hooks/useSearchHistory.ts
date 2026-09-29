import { useMemo, useSyncExternalStore } from "react"

import { clearSearches, getSearches, loadSearch, removeSearch, subscribe } from "@/lib/searchHistory"

/** Recent searches, kept in sync with localStorage (including changes made in other tabs). */
export function useSearchHistory() {
  const searches = useSyncExternalStore(subscribe, getSearches)
  return useMemo(() => ({ searches, load: loadSearch, remove: removeSearch, clear: clearSearches }), [searches])
}
