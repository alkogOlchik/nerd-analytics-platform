import { apiClient } from "data/apiClient"
import type {
  ApiChatResponse,
  ChatSessionDto,
  MessageDto,
  SendMessageRequest,
  CreateSessionRequest,
  SendMessageResponse,
  CreateSessionResponse,
  UploadedFileDto,
  EscalationOffer,
  EscalateChatRequest,
  EscalateChatResponse,
} from "./types"

export const assistantSource = {
  uploadFiles: async (files: File[]): Promise<UploadedFileDto[]> => {
    const form = new FormData()
    files.forEach((f) => form.append("files", f))
    const { data } = await apiClient.post<UploadedFileDto[]>("/ai/files", form, {
      headers: { "Content-Type": undefined },
    })
    return data
  },

  getSessions: async (): Promise<ChatSessionDto[]> => {
    const { data } = await apiClient.get<ChatSessionDto[]>("/ai/chat/sessions")
    return data
  },

  getMessages: async (chatId: string): Promise<MessageDto[]> => {
    const { data } = await apiClient.get<MessageDto[]>("/ai/chat/history", {
      params: { chat_id: chatId },
    })
    return data
  },

  sendMessage: async (req: SendMessageRequest): Promise<SendMessageResponse> => {
    const { data } = await apiClient.post<ApiChatResponse>("/ai/chat", {
      message: req.content,
      model: "gemma4:e2b",
      chat_id: req.chat_id,
      ...(req.file_ids?.length ? { file_ids: req.file_ids } : {}),
    })
    return {
      user_message: data.user_message,
      assistant_message: data.assistant_message,
      ticket_id: data.ticket_id,
      ticket_status: data.ticket_status,
      ticket_title: data.ticket_title,
      solution_offered: data.solution_offered ?? true,
      escalation: data.escalation ?? null,
    }
  },

  createSession: async (req: CreateSessionRequest): Promise<CreateSessionResponse> => {
    const { data } = await apiClient.post<ApiChatResponse>("/ai/chat", {
      message: req.first_message,
      model: "gemma4:e2b",
      ...(req.file_ids?.length ? { file_ids: req.file_ids } : {}),
    })

    const session: ChatSessionDto = {
      id: data.chat_id,
      title: data.ticket_title ?? (req.first_message.length > 40 ? req.first_message.slice(0, 40) + "…" : req.first_message),
      ticket_id: data.ticket_id,
      ticket_status: data.ticket_status,
      created_at: data.user_message.created_at,
      updated_at: data.assistant_message.created_at,
      last_message: data.assistant_message.message,
    }

    return {
      session,
      messages: [data.user_message, data.assistant_message],
      ticket_id: data.ticket_id,
      ticket_status: data.ticket_status,
      ticket_title: data.ticket_title,
      solution_offered: data.solution_offered ?? true,
      escalation: data.escalation ?? null,
    }
  },

  escalateChat: async (req: EscalateChatRequest): Promise<EscalateChatResponse> => {
    const { data } = await apiClient.post<EscalateChatResponse>("/ai/chat/escalate", {
      chat_id: req.chat_id,
      product: req.product,
      user_priority: req.user_priority,
      category: req.category,
      description: req.description,
    })
    return data
  },

  resolveChat: async (chatId: string): Promise<{ ticket_id: string; status: string }> => {
    const { data } = await apiClient.post(`/ai/chat/${chatId}/resolve`)
    return data
  },

  escalateToOperator: async (chatId: string): Promise<{ ticket_id: string; status: string }> => {
    const { data } = await apiClient.post(`/ai/chat/${chatId}/operator`)
    return data
  },
}

export type {
  ChatSessionDto,
  MessageDto,
  SendMessageRequest,
  CreateSessionRequest,
  SendMessageResponse,
  CreateSessionResponse,
  UploadedFileDto,
  EscalationOffer,
  EscalateChatRequest,
  EscalateChatResponse,
}
