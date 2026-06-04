import { useState, useRef, useEffect } from "react"
import { useLocation } from "react-router-dom"
import { Bot, User2 } from "lucide-react"
import styles from "./AssistantScreen.module.scss"
import { Sidebar, UserMenu } from "modules"
import { ChatHistory } from "modules/ChatHistory"
import { ChatMessage } from "modules/ChatMessage"
import { ChatInput } from "modules/ChatInput"
import { useChatSessions } from "domain/Assistant/useChatSessions"
import { useMessages } from "domain/Assistant/useMessages"
import { useSendMessage } from "domain/Assistant/useSendMessage"
import { useCreateSession } from "domain/Assistant/useCreateSession"
import type { CreateSessionResult } from "data/repositories/Assistant"

export const AssistantScreen = () => {
  // undefined = initial (fall back to sessions[0]), null = explicitly "new chat", string = selected session
  const [activeSessionId, setActiveSessionId] = useState<string | null | undefined>(undefined)
  const [inputValue, setInputValue] = useState("")
  const [pendingFirstMessage, setPendingFirstMessage] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const location = useLocation()
  const autoSentRef = useRef(false)

  const { data: sessions = [], isLoading: sessionsLoading } = useChatSessions()

  const effectiveSessionId =
    activeSessionId !== undefined ? activeSessionId : (sessions[0]?.id ?? null)

  const { data: messages = [], isLoading: messagesLoading } = useMessages(effectiveSessionId)
  const sendMessage = useSendMessage(effectiveSessionId)

  const handleSessionCreated = (result: CreateSessionResult) => {
    setActiveSessionId(result.session.id)
    setInputValue("")
    setPendingFirstMessage(null)
  }

  const createSession = useCreateSession(handleSessionCreated)

  // Auto-send message passed from PromptCard on the main screen
  useEffect(() => {
    if (autoSentRef.current) return
    const initialMsg = (location.state as { initialMessage?: string })?.initialMessage
    if (initialMsg?.trim()) {
      autoSentRef.current = true
      setPendingFirstMessage(initialMsg)
      createSession.mutate(initialMsg)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, pendingFirstMessage])

  const handleSend = () => {
    const text = inputValue.trim()
    if (!text) return

    if (!effectiveSessionId) {
      setPendingFirstMessage(text)
      setInputValue("")
      createSession.mutate(text)
    } else {
      sendMessage.mutate(text)
      setInputValue("")
    }
  }

  const handleNewChat = () => {
    setActiveSessionId(null)
    setInputValue("")
    setPendingFirstMessage(null)
  }

  const isSending = sendMessage.isPending || createSession.isPending

  const activeSession = sessions.find((s) => s.id === effectiveSessionId)

  // Deduplicate messages by id as a safety net
  const uniqueMessages = messages.filter(
    (msg, idx, arr) => arr.findIndex((m) => m.id === msg.id) === idx,
  )

  return (
    <div className={styles.page}>
      <Sidebar />
      <ChatHistory
        sessions={sessions}
        activeSessionId={effectiveSessionId}
        isLoading={sessionsLoading}
        onSelect={setActiveSessionId}
        onNewChat={handleNewChat}
      />

      <main className={styles.main}>
        <div className={styles.mainHeader}>
          <div className={styles.chatTitle}>
            {activeSession ? (
              <h1 className={styles.sessionTitle}>{activeSession.title}</h1>
            ) : (
              <h1 className={styles.sessionTitle}>Новый чат</h1>
            )}
          </div>
          <UserMenu />
        </div>

        <div className={styles.messagesArea}>
          {!effectiveSessionId && !isSending && !pendingFirstMessage && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>
                <Bot size={40} />
              </div>
              <h2 className={styles.emptyTitle}>Чем могу помочь?</h2>
              <p className={styles.emptySubtitle}>
                Опишите вашу проблему — я постараюсь помочь
              </p>
            </div>
          )}

          {messagesLoading && (
            <div className={styles.loadingMessages}>
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
            </div>
          )}

          {!messagesLoading &&
            uniqueMessages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

          {pendingFirstMessage && createSession.isPending && (
            <div className={styles.pendingUserMessage}>
              <div className={styles.pendingBubble}>
                <p className={styles.pendingText}>{pendingFirstMessage}</p>
              </div>
              <div className={styles.pendingAvatar}>
                <User2 size={18} />
              </div>
            </div>
          )}

          {isSending && (
            <div className={styles.typingIndicator}>
              <div className={styles.typingAvatar}>
                <Bot size={16} />
              </div>
              <div className={styles.typingBubble}>
                <span className={styles.typingDot} />
                <span className={styles.typingDot} />
                <span className={styles.typingDot} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSend}
          disabled={isSending}
        />
      </main>
    </div>
  )
}
