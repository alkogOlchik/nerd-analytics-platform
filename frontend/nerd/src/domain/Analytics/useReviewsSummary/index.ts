import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useReviewsSummary = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "reviewsSummary", filters ?? {}],
    queryFn: () => analyticsRepository.getReviewsSummary(filters),
    staleTime: 60_000,
  })
