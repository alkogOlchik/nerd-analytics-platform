import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useUsersRetention = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "usersRetention", filters ?? {}],
    queryFn: () => analyticsRepository.getUserRetention(filters),
    staleTime: 60_000,
  })
