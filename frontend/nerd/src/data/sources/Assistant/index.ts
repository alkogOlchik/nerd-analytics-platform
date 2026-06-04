import { apiClient } from "data/apiClient"
import type {
  ChatSessionDto,
  MessageDto,
  SendMessageRequest,
  CreateSessionRequest,
  SendMessageResponse,
  CreateSessionResponse,
  UploadedFileDto,
} from "./types"

const SESSIONS_KEY = "nerd_chat_sessions"

const loadSessions = (): ChatSessionDto[] => {
  try {
    return JSON.parse(localStorage.getItem(SESSIONS_KEY) ?? "[]") as ChatSessionDto[]
  } catch {
    return []
  }
}

const saveSessions = (sessions: ChatSessionDto[]) => {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions))
}

interface ApiChatResponse {
  chat_id: string
  user_message: MessageDto
  assistant_message: MessageDto
  ml_response: Record<string, unknown>
}

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
    return [...loadSessions()].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    )
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

    const sessions = loadSessions()
    const session = sessions.find((s) => s.id === req.chat_id)
    if (session) {
      session.last_message = data.assistant_message.message
      session.updated_at = data.assistant_message.created_at
      saveSessions(sessions)
    }

    return { user_message: data.user_message, assistant_message: data.assistant_message }
  },

  createSession: async (req: CreateSessionRequest): Promise<CreateSessionResponse> => {
    const { data } = await apiClient.post<ApiChatResponse>("/ai/chat", {
      message: req.first_message,
      model: "gemma4:e2b",
      ...(req.file_ids?.length ? { file_ids: req.file_ids } : {}),
    })

    const title =
      req.first_message.length > 40 ? req.first_message.slice(0, 40) + "…" : req.first_message

    const session: ChatSessionDto = {
      id: data.chat_id,
      title,
      created_at: data.user_message.created_at,
      updated_at: data.assistant_message.created_at,
      last_message: data.assistant_message.message,
    }

    const sessions = loadSessions()
    sessions.unshift(session)
    saveSessions(sessions)

    return { session, messages: [data.user_message, data.assistant_message] }
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
}
