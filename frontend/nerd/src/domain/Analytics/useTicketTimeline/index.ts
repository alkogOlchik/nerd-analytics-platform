import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"
import type { AnalyticsFilters } from "data/repositories/Analytics"

export const useTicketTimeline = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: ["analytics", "ticketTimeline", filters ?? {}],
    queryFn: () => analyticsRepository.getTicketTimeline(filters),
    staleTime: 60_000,
  })
