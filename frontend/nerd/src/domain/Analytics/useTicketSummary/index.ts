import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useTicketSummary = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "ticketSummary", filters ?? {}],
    queryFn: () => analyticsRepository.getTicketSummary(filters),
    staleTime: 60_000,
  })
