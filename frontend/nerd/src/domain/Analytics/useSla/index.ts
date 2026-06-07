import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useSla = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "sla", filters ?? {}],
    queryFn: () => analyticsRepository.getSla(filters),
    staleTime: 60_000,
  })
