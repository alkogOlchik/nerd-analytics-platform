import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useAiAccuracy = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "aiAccuracy", filters ?? {}],
    queryFn: () => analyticsRepository.getAiAccuracy(filters),
    staleTime: 60_000,
  })
