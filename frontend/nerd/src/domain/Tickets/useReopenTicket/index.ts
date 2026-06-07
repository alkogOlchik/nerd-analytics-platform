import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ticketsRepository } from "data/repositories/Tickets"
import { TICKETS_QUERY_KEY } from "../useTickets"

export const useReopenTicket = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => ticketsRepository.reopenTicket(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TICKETS_QUERY_KEY })
    },
  })
}
