import { useState, useRef, useEffect } from "react"
import { useLocation } from "react-router-dom"
import { Bot, User2, CheckCircle, Clock } from "lucide-react"
import styles from "./AssistantScreen.module.scss"
import { Sidebar, UserMenu } from "modules"
import { ChatHistory } from "modules/ChatHistory"
import { ChatMessage } from "modules/ChatMessage"
import { ChatInput } from "modules/ChatInput"
import { useChatSessions } from "domain/Assistant/useChatSessions"
import { useMessages } from "domain/Assistant/useMessages"
import { useSendMessage } from "domain/Assistant/useSendMessage"
import { useCreateSession } from "domain/Assistant/useCreateSession"
import { useResolveChat } from "domain/Assistant/useResolveChat"
import type { CreateSessionResult } from "data/repositories/Assistant"

export const AssistantScreen = () => {
  const [activeSessionId, setActiveSessionId] = useState<string | null | undefined>(undefined)
  const [inputValue, setInputValue] = useState("")
  const [pendingFirstMessage, setPendingFirstMessage] = useState<string | null>(null)
  const [ticketId, setTicketId] = useState<string | null>(null)
  const [ticketStatus, setTicketStatus] = useState<string | null>(null)
  const [ticketTitle, setTicketTitle] = useState<string | null>(null)
  const [solutionOffered, setSolutionOffered] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const location = useLocation()
  const autoSentRef = useRef(false)

  const { data: sessions = [], isLoading: sessionsLoading } = useChatSessions()

  const effectiveSessionId =
    activeSessionId !== undefined ? activeSessionId : (sessions[0]?.id ?? null)

  const { data: messages = [], isLoading: messagesLoading } = useMessages(effectiveSessionId)
  const sendMessage = useSendMessage(effectiveSessionId)
  const { mutate: resolveChat, isPending: isResolving } = useResolveChat()

  // Sync ticket state from sessions when switching sessions
  useEffect(() => {
    if (!effectiveSessionId) {
      setTicketId(null)
      setTicketStatus(null)
      setTicketTitle(null)
      setSolutionOffered(false)
      return
    }
    const session = sessions.find((s) => s.id === effectiveSessionId)
    if (session) {
      setTicketId(session.ticketId)
      setTicketStatus(session.ticketStatus)
    }
  }, [effectiveSessionId, sessions])

  // Update ticket state after sending a message
  useEffect(() => {
    if (sendMessage.data) {
      const d = sendMessage.data
      if (d.ticketId !== undefined) setTicketId(d.ticketId)
      if (d.ticketStatus !== undefined) setTicketStatus(d.ticketStatus)
      if (d.ticketTitle !== undefined) setTicketTitle(d.ticketTitle)
      setSolutionOffered(d.solutionOffered)
    }
  }, [sendMessage.data])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, pendingFirstMessage])

  const handleSessionCreated = (result: CreateSessionResult) => {
    setActiveSessionId(result.session.id)
    setInputValue("")
    setPendingFirstMessage(null)
    setTicketId(result.ticketId)
    setTicketStatus(result.ticketStatus)
    setTicketTitle(result.ticketTitle)
    setSolutionOffered(result.solutionOffered)
  }

  const createSession = useCreateSession(handleSessionCreated)

  useEffect(() => {
    if (autoSentRef.current) return
    const initialMsg = (location.state as { initialMessage?: string })?.initialMessage
    if (initialMsg?.trim()) {
      autoSentRef.current = true
      setPendingFirstMessage(initialMsg)
      createSession.mutate({ firstMessage: initialMsg })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSend = (files: File[]) => {
    const text = inputValue.trim()
    if (!text && files.length === 0) return

    if (!effectiveSessionId) {
      setPendingFirstMessage(text || `[${files.map((f) => f.name).join(", ")}]`)
      setInputValue("")
      createSession.mutate({ firstMessage: text, files })
    } else {
      sendMessage.mutate({ content: text, files })
      setInputValue("")
    }
  }

  const handleNewChat = () => {
    setActiveSessionId(null)
    setInputValue("")
    setPendingFirstMessage(null)
    setTicketId(null)
    setTicketStatus(null)
    setTicketTitle(null)
    setSolutionOffered(false)
  }

  const handleResolve = () => {
    if (!effectiveSessionId) return
    resolveChat(effectiveSessionId, {
      onSuccess: () => setTicketStatus("closed"),
    })
  }

  const isSending = sendMessage.isPending || createSession.isPending
  const isChatClosed = ticketStatus === "closed"
  const isWaitingForOperator = ticketStatus === "waiting_for_operator"
  const isChatBlocked = isChatClosed || isWaitingForOperator
  const activeSession = sessions.find((s) => s.id === effectiveSessionId)

  const uniqueMessages = messages.filter(
    (msg, idx, arr) => arr.findIndex((m) => m.id === msg.id) === idx,
  )

  const hasAssistantResponse = uniqueMessages.some((m) => m.role === "assistant")
  const showResolveButton =
    !isSending &&
    !isChatBlocked &&
    solutionOffered &&
    hasAssistantResponse &&
    !!effectiveSessionId

  return (
    <div className={styles.page}>
      <Sidebar />
      <ChatHistory
        sessions={sessions}
        activeSessionId={effectiveSessionId}
        isLoading={sessionsLoading}
        onSelect={(id) => {
          setActiveSessionId(id)
          setTicketId(null)
          setTicketStatus(null)
          setTicketTitle(null)
          setSolutionOffered(false)
        }}
        onNewChat={handleNewChat}
      />

      <main className={styles.main}>
        <div className={styles.mainHeader}>
          <div className={styles.chatTitle}>
            {activeSession ? (
              <h1 className={styles.sessionTitle}>{ticketTitle ?? activeSession.title}</h1>
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

          {isChatClosed && (
            <div className={`${styles.systemBanner} ${styles.bannerClosed}`}>
              <CheckCircle size={16} />
              Рад помочь! Обращение закрыто.
            </div>
          )}

          {isWaitingForOperator && (
            <div className={`${styles.systemBanner} ${styles.bannerWaiting}`}>
              <Clock size={16} />
              Обращение передано оператору. Ожидайте ответа.
            </div>
          )}

          {showResolveButton && (
            <div className={styles.resolveBar}>
              <button
                className={styles.resolveButton}
                onClick={handleResolve}
                disabled={isResolving}
              >
                {isResolving ? "Закрываем..." : "✓ Проблема решена"}
              </button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSend}
          disabled={isSending || isChatBlocked}
        />
      </main>
    </div>
  )
}
