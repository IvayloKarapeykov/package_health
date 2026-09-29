import { useCallback, useEffect, useState } from "react"

import { readString, writeString } from "@/lib/storage"

export type Theme = "light" | "dark"

const STORAGE_KEY = "package-health-theme"

function readInitialTheme(): Theme {
  const stored = readString(STORAGE_KEY)
  if (stored === "light" || stored === "dark") return stored
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(readInitialTheme)

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
    writeString(STORAGE_KEY, theme)
  }, [theme])

  const toggleTheme = useCallback(() => setTheme((current) => (current === "dark" ? "light" : "dark")), [])

  return { theme, toggleTheme }
}
