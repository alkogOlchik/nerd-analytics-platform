import { useQuery } from "@tanstack/react-query"
import { analyticsRepository } from "data/repositories/Analytics"

export const useTicketForecast = (params?: { product?: string; category?: string }) =>
  useQuery({
    queryKey: ["analytics", "ticketForecast", params ?? {}],
    queryFn: () => analyticsRepository.getTicketForecast(params),
    staleTime: 60_000,
  })
