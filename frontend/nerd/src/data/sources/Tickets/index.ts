import { apiClient } from "data/apiClient"
import type {
  TicketDto,
  CreateTicketRequest,
  UpdateTicketRequest,
  ClassifyTicketRequest,
  AddCommentRequest,
  PatchStatusRequest,
  PatchPriorityRequest,
  StatusHistoryDto,
  CommentDto,
  GuestTicketCreateRequest,
  GuestTicketResponse,
  GuestTrackResponse,
} from "./types"

export const ticketsSource = {
  createGuestTicket: (req: GuestTicketCreateRequest) =>
    apiClient.post<GuestTicketResponse>("/tickets/guest", req).then((r) => r.data),

  trackGuestTicket: (token: string) =>
    apiClient.get<GuestTrackResponse>(`/tickets/track/${token}`).then((r) => r.data),
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

  addComment: (id: string, req: AddCommentRequest) =>
    apiClient.post<CommentDto>(`/tickets/${id}/comments`, req).then((r) => r.data),

  patchStatus: (id: string, req: PatchStatusRequest) =>
    apiClient.patch<TicketDto>(`/tickets/${id}/status`, req).then((r) => r.data),

  patchPriority: (id: string, req: PatchPriorityRequest) =>
    apiClient.patch<TicketDto>(`/tickets/${id}/priority`, req).then((r) => r.data),

  getStatusHistory: (id: string) =>
    apiClient.get<StatusHistoryDto[]>(`/tickets/${id}/status-history`).then((r) => r.data),
}

export type {
  TicketDto,
  CreateTicketRequest,
  UpdateTicketRequest,
  ClassifyTicketRequest,
  AddCommentRequest,
  PatchStatusRequest,
  PatchPriorityRequest,
  StatusHistoryDto,
  CommentDto,
  GuestTicketCreateRequest,
  GuestTicketResponse,
  GuestTrackResponse,
}
