import { ticketsSource } from "data/sources/Tickets"
import type { TicketDto } from "data/sources/Tickets"
import type { Ticket } from "./types"

const mapTicket = (dto: TicketDto): Ticket => ({
  id: dto.id,
  category: dto.category,
  title: dto.title,
  description: dto.description,
  status: dto.status,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at,
})

export const ticketsRepository = {
  getTickets: async (): Promise<Ticket[]> => {
    const dtos = await ticketsSource.getTickets()
    return dtos.map(mapTicket)
  },
}

export type { Ticket, TicketCategory, TicketStatus } from "./types"
