export type TicketCategory = "complaint" | "support" | "review"
export type TicketStatus = "open" | "in_progress" | "closed"

export interface Ticket {
  id: string
  category: TicketCategory
  title: string
  description: string
  status: TicketStatus
  createdAt: string
  updatedAt: string
}
