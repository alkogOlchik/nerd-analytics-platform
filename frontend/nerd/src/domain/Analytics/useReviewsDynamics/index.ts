import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useReviewsDynamics = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "reviewsDynamics", filters ?? {}],
    queryFn: () => analyticsRepository.getReviewsDynamics(filters),
    staleTime: 60_000,
  })
