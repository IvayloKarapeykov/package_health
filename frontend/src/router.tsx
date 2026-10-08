import { createBrowserRouter, Navigate } from "react-router"

import { SiteLayout } from "@/components/layout/SiteLayout"

export const router = createBrowserRouter([
  {
    Component: SiteLayout,
    children: [
      { index: true, lazy: async () => ({ Component: (await import("@/pages/LandingPage")).default }) },
      { path: "app", lazy: async () => ({ Component: (await import("@/pages/AnalyzerPage")).default }) },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
])
