export type TicketStatusDto = "open" | "in_progress" | "closed" | "reopened"
export type TicketPriorityDto = "low" | "medium" | "high"
export type TicketProductDto =
  | "веб-сервис"
  | "платёжный сервис"
  | "мобильное приложение"
  | "API интеграция"
  | "личный кабинет"
  | "аналитический модуль"

export interface TicketDto {
  id: string
  client_id: string
  responsible_id: string | null
  product: TicketProductDto
  status: TicketStatusDto
  priority: TicketPriorityDto
  date: string
  deadline: string
  closed_at: string | null
  reopened_count: number
  last_reopened_at: string | null
  ai_suggested_category: string | null
  final_category: string | null
  is_admin_changed: boolean
  keywords: string[]
  confidence: number | null
  sla_ttfr_min: number | null
  sla_ttr_min: number | null
}

export interface CreateTicketRequest {
  product: TicketProductDto
  priority?: TicketPriorityDto
  deadline: string
  sla_ttfr_min?: number
  sla_ttr_min?: number
}

export interface UpdateTicketRequest {
  status?: TicketStatusDto
  priority?: TicketPriorityDto
  responsible_id?: string
  final_category?: string
  is_admin_changed?: boolean
  sla_ttfr_min?: number
}

export interface ClassifyTicketRequest {
  ticket_id: string
  text: string
  model?: string
}
