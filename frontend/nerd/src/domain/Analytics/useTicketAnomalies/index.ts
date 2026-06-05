import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useTicketAnomalies = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "ticketAnomalies", filters ?? {}],
    queryFn: () => analyticsRepository.getTicketAnomalies(filters),
    staleTime: 60_000,
  })
