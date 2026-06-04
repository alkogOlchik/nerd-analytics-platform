import { assistantSource } from "data/sources/Assistant"
import type { ChatSessionDto, MessageDto } from "data/sources/Assistant"
import type {
  ChatSession,
  Message,
  SendMessageResult,
  CreateSessionResult,
} from "./types"

const mapSession = (dto: ChatSessionDto): ChatSession => ({
  id: dto.id,
  title: dto.title,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at,
  lastMessage: dto.last_message,
})

const mapMessage = (dto: MessageDto): Message => ({
  id: dto.id,
  sessionId: dto.chat_id,
  role: dto.role === "client" ? "user" : "assistant",
  content: dto.message,
  createdAt: dto.created_at,
})

export const assistantRepository = {
  getSessions: async (): Promise<ChatSession[]> => {
    const dtos = await assistantSource.getSessions()
    return dtos.map(mapSession)
  },

  getMessages: async (sessionId: string): Promise<Message[]> => {
    const dtos = await assistantSource.getMessages(sessionId)
    return dtos.map(mapMessage)
  },

  sendMessage: async (sessionId: string, content: string, files?: File[]): Promise<SendMessageResult> => {
    let file_ids: string[] | undefined
    if (files?.length) {
      const uploaded = await assistantSource.uploadFiles(files)
      file_ids = uploaded.map((f) => f.id)
    }
    const res = await assistantSource.sendMessage({ chat_id: sessionId, content, file_ids })
    return {
      userMessage: mapMessage(res.user_message),
      assistantMessage: mapMessage(res.assistant_message),
    }
  },

  createSession: async (firstMessage: string, files?: File[]): Promise<CreateSessionResult> => {
    let file_ids: string[] | undefined
    if (files?.length) {
      const uploaded = await assistantSource.uploadFiles(files)
      file_ids = uploaded.map((f) => f.id)
    }
    const res = await assistantSource.createSession({ first_message: firstMessage, file_ids })
    return {
      session: mapSession(res.session),
      messages: res.messages.map(mapMessage),
    }
  },
}

export type { ChatSession, Message, SendMessageResult, CreateSessionResult }
