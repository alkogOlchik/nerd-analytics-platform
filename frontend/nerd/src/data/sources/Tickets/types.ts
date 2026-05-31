export type TicketCategoryDto = "complaint" | "support" | "review"
export type TicketStatusDto = "open" | "in_progress" | "closed"

export interface TicketDto {
  id: string
  category: TicketCategoryDto
  title: string
  description: string
  status: TicketStatusDto
  created_at: string
  updated_at: string
}
