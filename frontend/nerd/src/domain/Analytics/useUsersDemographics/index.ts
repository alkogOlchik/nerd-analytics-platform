import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useUsersDemographics = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "usersDemographics", filters ?? {}],
    queryFn: () => analyticsRepository.getUserDemographics(filters),
    staleTime: 60_000,
  })
