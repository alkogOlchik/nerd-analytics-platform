import { useQuery } from "@tanstack/react-query"
import { ticketsRepository } from "data/repositories/Tickets"

export const useGuestTicketTrack = (token: string | undefined) =>
  useQuery({
    queryKey: ["guest-ticket-track", token],
    queryFn: () => ticketsRepository.trackGuestTicket(token!),
    enabled: Boolean(token),
    retry: false,
  })
