import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ticketsRepository } from "data/repositories/Tickets"
import { TICKETS_QUERY_KEY } from "../useTickets"

export const useUpdateTicketStatus = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status, responsibleId }: { id: string; status: string; responsibleId?: string }) =>
      ticketsRepository.patchStatus(id, status, responsibleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TICKETS_QUERY_KEY })
    },
  })
}
