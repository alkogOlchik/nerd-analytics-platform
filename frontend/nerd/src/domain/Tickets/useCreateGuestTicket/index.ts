import { useMutation } from "@tanstack/react-query"
import { ticketsRepository } from "data/repositories/Tickets"
import type { GuestTicketInput, GuestTicketResult } from "data/repositories/Tickets"

export const useCreateGuestTicket = () =>
  useMutation<GuestTicketResult, Error, GuestTicketInput>({
    mutationFn: (input) => ticketsRepository.createGuestTicket(input),
  })
