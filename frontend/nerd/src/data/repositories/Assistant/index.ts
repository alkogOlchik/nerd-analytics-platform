import { assistantSource } from "data/sources/Assistant"
import type { ChatSessionDto, MessageDto, EscalationOffer } from "data/sources/Assistant"
import type {
  ChatSession,
  Message,
  SendMessageResult,
  CreateSessionResult,
  EscalationInfo,
  EscalateChatInput,
  EscalateChatResult,
} from "./types"

const mapEscalation = (dto: EscalationOffer | null | undefined): EscalationInfo | null => {
  if (!dto) return null
  return {
    required: dto.required,
    suggestedProduct: dto.suggested_product,
    suggestedCategory: dto.suggested_category,
    confidence: dto.confidence,
    products: dto.products,
    categories: dto.categories,
    priorities: dto.priorities,
    priorityLabels: dto.priority_labels,
  }
}

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
      escalation: mapEscalation(res.escalation),
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
      escalation: mapEscalation(res.escalation),
    }
  },

  escalateChat: async (input: EscalateChatInput): Promise<EscalateChatResult> => {
    const res = await assistantSource.escalateChat({
      chat_id: input.chatId,
      product: input.product,
      user_priority: input.userPriority,
      category: input.category,
      description: input.description,
    })
    return {
      ticketId: res.ticket_id,
      status: res.status,
      aiSuggestedCategory: res.ai_suggested_category,
      finalCategory: res.final_category,
    }
  },
}

export type { ChatSession, Message, SendMessageResult, CreateSessionResult, EscalationInfo, EscalateChatInput, EscalateChatResult }
