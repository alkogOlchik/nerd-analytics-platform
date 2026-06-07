import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ticketsRepository } from "data/repositories/Tickets"
import type { CreateTicketInput } from "data/repositories/Tickets"
import { TICKETS_QUERY_KEY } from "../useTickets"

export const useCreateTicket = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: CreateTicketInput & { description?: string }) => {
      const ticket = await ticketsRepository.createTicket(input)
      if (input.description?.trim()) {
        await ticketsRepository.addComment(ticket.id, input.description.trim())
      }
      return ticket
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TICKETS_QUERY_KEY })
    },
  })
}
