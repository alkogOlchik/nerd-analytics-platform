import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useAiEfficiency = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "aiEfficiency", filters ?? {}],
    queryFn: () => analyticsRepository.getAiEfficiency(filters),
    staleTime: 60_000,
  })
