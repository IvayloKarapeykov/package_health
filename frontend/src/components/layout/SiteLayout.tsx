import { Outlet, ScrollRestoration } from "react-router"

import { AppBackground } from "@/components/layout/AppBackground"
import { SiteNav } from "@/components/layout/SiteNav"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Wordmark } from "@/components/layout/Wordmark"
import { useTheme } from "@/hooks/useTheme"

export function SiteLayout() {
  const { theme, toggleTheme } = useTheme()
  return (
    <div className="relative min-h-svh">
      <AppBackground />
      <Wordmark className="fixed top-4 left-4 z-20" />
      <div className="fixed top-4 right-4 z-20 flex items-center gap-2">
        <SiteNav />
        <ThemeToggle theme={theme} onToggle={toggleTheme} />
      </div>
      <Outlet />
      <ScrollRestoration />
    </div>
  )
}
