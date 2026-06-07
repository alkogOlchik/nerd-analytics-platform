import { useMutation } from "@tanstack/react-query"
import { ticketsRepository } from "data/repositories/Tickets"

export const useAddTicketComment = () =>
  useMutation({
    mutationFn: ({ id, message }: { id: string; message: string }) =>
      ticketsRepository.addComment(id, message),
  })
