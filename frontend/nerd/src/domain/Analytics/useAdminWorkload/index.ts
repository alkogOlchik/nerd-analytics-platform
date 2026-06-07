import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useAdminWorkload = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "adminWorkload", filters ?? {}],
    queryFn: () => analyticsRepository.getAdminWorkload(filters),
    staleTime: 60_000,
  })
