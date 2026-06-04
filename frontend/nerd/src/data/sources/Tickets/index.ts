import { apiClient } from "data/apiClient"
import type { TicketDto, CreateTicketRequest, UpdateTicketRequest, ClassifyTicketRequest } from "./types"

export const ticketsSource = {
  getTickets: (params?: {
    status?: string
    priority?: string
    product?: string
    category?: string
    skip?: number
    limit?: number
  }) =>
    apiClient
      .get<TicketDto[]>("/tickets", { params: { limit: 100, ...params } })
      .then((r) => r.data),

  getTicket: (id: string) =>
    apiClient.get<TicketDto>(`/tickets/${id}`).then((r) => r.data),

  createTicket: (req: CreateTicketRequest) =>
    apiClient.post<TicketDto>("/tickets", req).then((r) => r.data),

  updateTicket: (id: string, req: UpdateTicketRequest) =>
    apiClient.patch<TicketDto>(`/tickets/${id}`, req).then((r) => r.data),

  reopenTicket: (id: string) =>
    apiClient.post<TicketDto>(`/tickets/${id}/reopen`).then((r) => r.data),

  classifyTicket: (req: ClassifyTicketRequest) =>
    apiClient.post<TicketDto>("/ai/classify/ticket", req).then((r) => r.data),

  getTicketClassification: (ticketId: string) =>
    apiClient
      .get<Pick<TicketDto, "id" | "ai_suggested_category" | "final_category" | "is_admin_changed" | "keywords" | "confidence">>(
        `/ai/classify/ticket/${ticketId}`,
      )
      .then((r) => r.data),
}

export type { TicketDto, CreateTicketRequest, UpdateTicketRequest, ClassifyTicketRequest }
