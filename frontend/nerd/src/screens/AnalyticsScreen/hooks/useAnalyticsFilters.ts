import { useState, useCallback } from "react"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useAnalyticsFilters = (dashboardId: string) => {
  const storageKey = `analytics-filters-${dashboardId}`

  const [filters, setFilters] = useState<AnalyticsFilters>(() => {
    try {
      const saved = localStorage.getItem(storageKey)
      return saved ? (JSON.parse(saved) as AnalyticsFilters) : {}
    } catch {
      return {}
    }
  })

  const updateFilters = useCallback((next: Partial<AnalyticsFilters>) => {
    setFilters((prev) => ({ ...prev, ...next }))
  }, [])

  const resetFilters = useCallback(() => setFilters({}), [])

  const saveConfig = useCallback(() => {
    localStorage.setItem(storageKey, JSON.stringify(filters))
  }, [filters, storageKey])

  return { filters, updateFilters, resetFilters, saveConfig }
}
