import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useReviewsKeywords = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "reviewsKeywords", filters ?? {}],
    queryFn: () => analyticsRepository.getReviewsKeywords(filters),
    staleTime: 60_000,
  })
