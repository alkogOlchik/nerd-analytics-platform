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
import { useEscalateChat } from "domain/Assistant/useEscalateChat"
import type { CreateSessionResult, EscalationInfo } from "data/repositories/Assistant"

const PRODUCTS = [
  "веб-сервис",
  "платёжный сервис",
  "мобильное приложение",
  "API интеграция",
  "личный кабинет",
  "аналитический модуль",
]

const PRIORITY_LABELS: Record<string, string> = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
}

const EscalationBanner = ({
  chatId,
  info,
  onDismiss,
  onSuccess,
}: {
  chatId: string
  info: EscalationInfo
  onDismiss: () => void
  onSuccess: (ticketId: string) => void
}) => {
  const [product, setProduct] = useState(info.suggestedProduct ?? "")
  const [priority, setPriority] = useState(info.priorities[0] ?? "medium")
  const [category, setCategory] = useState(info.suggestedCategory ?? "")
  const [description, setDescription] = useState("")

  const { mutateAsync: escalate, isPending } = useEscalateChat()

  const handleSubmit = async () => {
    if (!product) return
    const res = await escalate({
      chatId,
      product,
      userPriority: priority,
      category: category || undefined,
      description: description || undefined,
    })
    onSuccess(res.ticketId)
  }

  const priorityOptions = info.priorities.length > 0 ? info.priorities : ["low", "medium", "high"]

  return (
    <div className={styles.escalationBanner}>
      <p className={styles.escalationTitle}>Передать специалисту</p>

      <div className={styles.escalationFields}>
        <div className={styles.escalationField}>
          <span className={styles.escalationLabel}>Продукт</span>
          <select
            className={styles.escalationSelect}
            value={product}
            onChange={(e) => setProduct(e.target.value)}
          >
            <option value="">Выберите...</option>
            {(info.products.length > 0 ? info.products : PRODUCTS).map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        <div className={styles.escalationField}>
          <span className={styles.escalationLabel}>Приоритет</span>
          <select
            className={styles.escalationSelect}
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            {priorityOptions.map((p) => (
              <option key={p} value={p}>
                {info.priorityLabels[p] ?? PRIORITY_LABELS[p] ?? p}
              </option>
            ))}
          </select>
        </div>

        {info.categories.length > 0 && (
          <div className={styles.escalationField}>
            <span className={styles.escalationLabel}>Категория</span>
            <select
              className={styles.escalationSelect}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">Из контекста</option>
              {info.categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        )}

        <div className={styles.escalationField} style={{ gridColumn: "1 / -1" }}>
          <span className={styles.escalationLabel}>Описание (необязательно)</span>
          <input
            className={styles.escalationInput}
            type="text"
            placeholder="Дополнительные детали..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
      </div>

      <div className={styles.escalationActions}>
        <button className={styles.escalationCancel} onClick={onDismiss}>
          Отмена
        </button>
        <button
          className={styles.escalationSubmit}
          disabled={isPending || !product}
          onClick={handleSubmit}
        >
          {isPending ? "Создаём..." : "Создать обращение"}
        </button>
      </div>
    </div>
  )
}

export const AssistantScreen = () => {
  const [activeSessionId, setActiveSessionId] = useState<string | null | undefined>(undefined)
  const [inputValue, setInputValue] = useState("")
  const [pendingFirstMessage, setPendingFirstMessage] = useState<string | null>(null)
  const [escalation, setEscalation] = useState<EscalationInfo | null>(null)
  const [escalationTicketId, setEscalationTicketId] = useState<string | null>(null)
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
    if (result.escalation?.required) {
      setEscalation(result.escalation)
      setEscalationTicketId(null)
    }
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

  useEffect(() => {
    if (sendMessage.data?.escalation?.required) {
      setEscalation(sendMessage.data.escalation)
      setEscalationTicketId(null)
    }
  }, [sendMessage.data])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, pendingFirstMessage])

  const handleSend = (files: File[]) => {
    const text = inputValue.trim()
    if (!text && files.length === 0) return
    setEscalation(null)
    setEscalationTicketId(null)

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
    setEscalation(null)
    setEscalationTicketId(null)
  }

  const isSending = sendMessage.isPending || createSession.isPending
  const activeSession = sessions.find((s) => s.id === effectiveSessionId)

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
        onSelect={(id) => {
          setActiveSessionId(id)
          setEscalation(null)
          setEscalationTicketId(null)
        }}
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

          {escalationTicketId && (
            <p className={styles.escalationSuccess}>
              ✓ Обращение создано. Специалист свяжется с вами.
            </p>
          )}

          {!isSending && escalation && !escalationTicketId && effectiveSessionId && (
            <EscalationBanner
              chatId={effectiveSessionId}
              info={escalation}
              onDismiss={() => setEscalation(null)}
              onSuccess={(ticketId) => {
                setEscalation(null)
                setEscalationTicketId(ticketId)
              }}
            />
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
