import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useAdminSla = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "adminSla", filters ?? {}],
    queryFn: () => analyticsRepository.getAdminSla(filters),
    staleTime: 60_000,
  })
