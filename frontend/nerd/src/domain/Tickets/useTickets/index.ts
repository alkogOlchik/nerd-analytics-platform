import { useQuery } from "@tanstack/react-query"
import { ticketsRepository } from "data/repositories/Tickets"

export const TICKETS_QUERY_KEY = ["tickets"] as const

export const useTickets = () => {
  return useQuery({
    queryKey: TICKETS_QUERY_KEY,
    queryFn: ticketsRepository.getTickets,
    staleTime: 60 * 1000,
  })
}
