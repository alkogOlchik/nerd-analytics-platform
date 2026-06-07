export type TicketStatus = "open" | "in_progress" | "closed" | "reopened"
export type TicketPriority = "low" | "medium" | "high"
export type TicketProduct =
  | "веб-сервис"
  | "платёжный сервис"
  | "мобильное приложение"
  | "API интеграция"
  | "личный кабинет"
  | "аналитический модуль"

export interface Ticket {
  id: string
  clientId: string
  responsibleId: string | null
  product: TicketProduct
  status: TicketStatus
  priority: TicketPriority
  date: string
  deadline: string
  closedAt: string | null
  reopenedCount: number
  aiSuggestedCategory: string | null
  finalCategory: string | null
  isAdminChanged: boolean
  keywords: string[]
  confidence: number | null
  slaTtfrMin: number | null
  slaTtrMin: number | null
}

export interface CreateTicketInput {
  product: TicketProduct
  priority?: TicketPriority
  deadline: string
  slaTtfrMin?: number
  slaTtrMin?: number
}

export interface UpdateTicketInput {
  status?: TicketStatus
  priority?: TicketPriority
  responsibleId?: string
  finalCategory?: string
  isAdminChanged?: boolean
  slaTtfrMin?: number
}

export interface StatusHistoryEntry {
  id: string
  ticketId: string | null
  statusFrom: string | null
  statusTo: string | null
  changedBy: string | null
  createdAt: string
}
