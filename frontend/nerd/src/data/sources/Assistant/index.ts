import {
  MOCK_SESSIONS,
  MOCK_MESSAGES,
  MOCK_ASSISTANT_REPLIES,
} from "./constants"
import type {
  ChatSessionDto,
  MessageDto,
  SendMessageRequest,
  CreateSessionRequest,
  SendMessageResponse,
  CreateSessionResponse,
} from "./types"

const delay = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

const sessionStore: ChatSessionDto[] = [...MOCK_SESSIONS]
const messageStore: Record<string, MessageDto[]> = Object.fromEntries(
  Object.entries(MOCK_MESSAGES).map(([k, v]) => [k, [...v]])
)

const randomReply = (): string =>
  MOCK_ASSISTANT_REPLIES[Math.floor(Math.random() * MOCK_ASSISTANT_REPLIES.length)]

export const assistantSource = {
  getSessions: async (): Promise<ChatSessionDto[]> => {
    await delay(300)
    return [...sessionStore].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  },

  getMessages: async (sessionId: string): Promise<MessageDto[]> => {
    await delay(200)
    return messageStore[sessionId] ?? []
  },

  sendMessage: async (req: SendMessageRequest): Promise<SendMessageResponse> => {
    await delay(500)
    const now = new Date().toISOString()

    const userMessage: MessageDto = {
      id: `msg-${Date.now()}-user`,
      session_id: req.session_id,
      role: "user",
      content: req.content,
      created_at: now,
    }

    await delay(700)
    const assistantReplyTime = new Date().toISOString()
    const assistantMessage: MessageDto = {
      id: `msg-${Date.now()}-assistant`,
      session_id: req.session_id,
      role: "assistant",
      content: randomReply(),
      created_at: assistantReplyTime,
    }

    if (!messageStore[req.session_id]) {
      messageStore[req.session_id] = []
    }
    messageStore[req.session_id].push(userMessage, assistantMessage)

    const session = sessionStore.find((s) => s.id === req.session_id)
    if (session) {
      session.last_message = assistantMessage.content
      session.updated_at = assistantReplyTime
    }

    return { user_message: userMessage, assistant_message: assistantMessage }
  },

  createSession: async (req: CreateSessionRequest): Promise<CreateSessionResponse> => {
    await delay(300)
    const now = new Date().toISOString()
    const sessionId = `session-${Date.now()}`

    const title =
      req.first_message.length > 40
        ? req.first_message.slice(0, 40) + "…"
        : req.first_message

    const session: ChatSessionDto = {
      id: sessionId,
      title,
      created_at: now,
      updated_at: now,
    }

    const userMessage: MessageDto = {
      id: `msg-${Date.now()}-user`,
      session_id: sessionId,
      role: "user",
      content: req.first_message,
      created_at: now,
    }

    await delay(700)
    const replyTime = new Date().toISOString()
    const assistantMessage: MessageDto = {
      id: `msg-${Date.now()}-assistant`,
      session_id: sessionId,
      role: "assistant",
      content: randomReply(),
      created_at: replyTime,
    }

    session.last_message = assistantMessage.content
    session.updated_at = replyTime

    sessionStore.unshift(session)
    messageStore[sessionId] = [userMessage, assistantMessage]

    return { session, messages: [userMessage, assistantMessage] }
  },
}

export type {
  ChatSessionDto,
  MessageDto,
  SendMessageRequest,
  CreateSessionRequest,
  SendMessageResponse,
  CreateSessionResponse,
}
