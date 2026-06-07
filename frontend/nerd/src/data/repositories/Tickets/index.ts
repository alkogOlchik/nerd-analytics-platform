import { ticketsSource } from "data/sources/Tickets"
import type { TicketDto, StatusHistoryDto } from "data/sources/Tickets"
import { MOCK_TICKETS } from "./mocks"
import type { Ticket, CreateTicketInput, UpdateTicketInput, StatusHistoryEntry } from "./types"

const IS_MOCK = import.meta.env.VITE_IS_MOCK === "true"

const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms))

const mapStatusHistory = (dto: StatusHistoryDto): StatusHistoryEntry => ({
  id: dto.id,
  ticketId: dto.ticket_id,
  statusFrom: dto.status_from,
  statusTo: dto.status_to,
  changedBy: dto.changed_by,
  createdAt: dto.created_at,
})

const mapTicket = (dto: TicketDto): Ticket => ({
  id: dto.id,
  clientId: dto.client_id,
  responsibleId: dto.responsible_id,
  product: dto.product,
  status: dto.status,
  priority: dto.priority,
  date: dto.date,
  deadline: dto.deadline,
  closedAt: dto.closed_at,
  reopenedCount: dto.reopened_count,
  aiSuggestedCategory: dto.ai_suggested_category,
  finalCategory: dto.final_category,
  isAdminChanged: dto.is_admin_changed,
  keywords: dto.keywords ?? [],
  confidence: dto.confidence,
  slaTtfrMin: dto.sla_ttfr_min,
  slaTtrMin: dto.sla_ttr_min,
})

const mockStore: Ticket[] = [...MOCK_TICKETS]

const mockRepository = {
  getTickets: async (): Promise<Ticket[]> => {
    await delay(300)
    return [...mockStore]
  },

  getTicket: async (id: string): Promise<Ticket> => {
    await delay(200)
    const ticket = mockStore.find((t) => t.id === id)
    if (!ticket) throw new Error(`Ticket ${id} not found`)
    return { ...ticket }
  },

  createTicket: async (input: CreateTicketInput): Promise<Ticket> => {
    await delay(300)
    const ticket: Ticket = {
      id: `ticket-${Date.now()}`,
      clientId: "mock-user-id",
      responsibleId: null,
      product: input.product,
      status: "open",
      priority: input.priority ?? "medium",
      date: new Date().toISOString(),
      deadline: input.deadline,
      closedAt: null,
      reopenedCount: 0,
      aiSuggestedCategory: null,
      finalCategory: null,
      isAdminChanged: false,
      keywords: [],
      confidence: null,
      slaTtfrMin: input.slaTtfrMin ?? null,
      slaTtrMin: input.slaTtrMin ?? null,
    }
    mockStore.push(ticket)
    return ticket
  },

  updateTicket: async (id: string, input: UpdateTicketInput): Promise<Ticket> => {
    await delay(200)
    const idx = mockStore.findIndex((t) => t.id === id)
    if (idx === -1) throw new Error(`Ticket ${id} not found`)
    mockStore[idx] = {
      ...mockStore[idx],
      ...(input.status && { status: input.status }),
      ...(input.priority && { priority: input.priority }),
      ...(input.responsibleId !== undefined && { responsibleId: input.responsibleId }),
      ...(input.finalCategory !== undefined && { finalCategory: input.finalCategory }),
      ...(input.isAdminChanged !== undefined && { isAdminChanged: input.isAdminChanged }),
    }
    return { ...mockStore[idx] }
  },

  reopenTicket: async (id: string): Promise<Ticket> => {
    await delay(200)
    const idx = mockStore.findIndex((t) => t.id === id)
    if (idx === -1) throw new Error(`Ticket ${id} not found`)
    mockStore[idx] = {
      ...mockStore[idx],
      status: "reopened",
      reopenedCount: mockStore[idx].reopenedCount + 1,
    }
    return { ...mockStore[idx] }
  },

  addComment: async (_id: string, _message: string): Promise<void> => {
    await delay(200)
  },

  patchStatus: async (id: string, status: string): Promise<Ticket> => {
    await delay(200)
    const idx = mockStore.findIndex((t) => t.id === id)
    if (idx === -1) throw new Error(`Ticket ${id} not found`)
    mockStore[idx] = { ...mockStore[idx], status: status as Ticket["status"] }
    return { ...mockStore[idx] }
  },

  getStatusHistory: async (_id: string): Promise<StatusHistoryEntry[]> => {
    await delay(200)
    return []
  },
}

const realRepository = {
  getTickets: async (params?: { status?: string; priority?: string; product?: string }): Promise<Ticket[]> => {
    const dtos = await ticketsSource.getTickets(params)
    return dtos.map(mapTicket)
  },

  getTicket: async (id: string): Promise<Ticket> => {
    const dto = await ticketsSource.getTicket(id)
    return mapTicket(dto)
  },

  createTicket: async (input: CreateTicketInput): Promise<Ticket> => {
    const dto = await ticketsSource.createTicket({
      product: input.product,
      priority: input.priority,
      deadline: input.deadline,
      sla_ttfr_min: input.slaTtfrMin,
      sla_ttr_min: input.slaTtrMin,
    })
    return mapTicket(dto)
  },

  updateTicket: async (id: string, input: UpdateTicketInput): Promise<Ticket> => {
    const dto = await ticketsSource.updateTicket(id, {
      status: input.status,
      priority: input.priority,
      responsible_id: input.responsibleId,
      final_category: input.finalCategory,
      is_admin_changed: input.isAdminChanged,
      sla_ttfr_min: input.slaTtfrMin,
    })
    return mapTicket(dto)
  },

  reopenTicket: async (id: string): Promise<Ticket> => {
    const dto = await ticketsSource.reopenTicket(id)
    return mapTicket(dto)
  },

  addComment: async (id: string, message: string): Promise<void> => {
    await ticketsSource.addComment(id, { message })
  },

  patchStatus: async (id: string, status: string, responsibleId?: string): Promise<Ticket> => {
    const dto = await ticketsSource.patchStatus(id, { status: status as TicketDto["status"], responsible_id: responsibleId })
    return mapTicket(dto)
  },

  patchPriority: async (id: string, adminPriority: string): Promise<Ticket> => {
    const dto = await ticketsSource.patchPriority(id, { admin_priority: adminPriority })
    return mapTicket(dto)
  },

  getStatusHistory: async (id: string): Promise<StatusHistoryEntry[]> => {
    const dtos = await ticketsSource.getStatusHistory(id)
    return dtos.map(mapStatusHistory)
  },
}

export const ticketsRepository = IS_MOCK ? mockRepository : realRepository

export type { Ticket, TicketStatus, TicketPriority, TicketProduct, CreateTicketInput, UpdateTicketInput, StatusHistoryEntry } from "./types"
