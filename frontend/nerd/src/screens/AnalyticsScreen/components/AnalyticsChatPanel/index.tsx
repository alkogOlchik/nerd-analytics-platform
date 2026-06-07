import { useState, useRef, useEffect } from "react"
import { Bot, Send } from "lucide-react"
import { apiClient } from "data/apiClient"
import styles from "./styles.module.scss"

interface ChatMsg {
  role: "user" | "assistant"
  text: string
  steps?: string[]
}

interface Props {
  context?: string
}

export const AnalyticsChatPanel = ({ context }: Props) => {
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: "user", text }])
    setInput("")
    setLoading(true)

    try {
      const message = context ? `${context}\n\nВопрос аналитика: ${text}` : text
      const { data } = await apiClient.post<{ answer: string; steps?: string[] | null }>("/ai/analytics/query", {
        message,
      })
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer, steps: data.steps ?? undefined },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Ошибка запроса. Попробуйте ещё раз." },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <aside className={styles.panel}>
      <div className={styles.panelHeader}>
        <Bot size={15} />
        <span>ИИ-ассистент</span>
      </div>

      <div className={styles.messages}>
        {messages.length === 0 && (
          <p className={styles.placeholder}>
            Задайте вопрос по данным дашборда или попросите посчитать метрику
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={msg.role === "user" ? styles.msgUser : styles.msgAssistant}
          >
            {msg.role === "assistant" && msg.steps && msg.steps.length > 0 && (
              <div className={styles.msgSteps}>
                {msg.steps.map((s, j) => (
                  <span key={j} className={styles.msgStep}>{s}</span>
                ))}
              </div>
            )}
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className={styles.msgAssistant}>
            <div className={styles.dots}>
              <span className={styles.dot} />
              <span className={styles.dot} />
              <span className={styles.dot} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className={styles.inputRow}>
        <textarea
          ref={inputRef}
          className={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Спросить ИИ..."
          rows={1}
          disabled={loading}
        />
        <button
          className={styles.sendBtn}
          onClick={send}
          disabled={!input.trim() || loading}
          aria-label="Отправить"
        >
          <Send size={15} />
        </button>
      </div>
    </aside>
  )
}
