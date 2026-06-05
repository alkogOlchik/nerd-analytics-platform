import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useDashboard6Tickets = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "dashboard6Tickets", filters ?? {}],
    queryFn: () => analyticsRepository.getDashboard6Tickets(filters),
    staleTime: 60_000,
  })
