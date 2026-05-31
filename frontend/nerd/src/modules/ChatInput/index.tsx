import { Send, Loader2, Mic, Plus } from "lucide-react"
import { type KeyboardEvent, useRef, useEffect } from "react"
import styles from "./styles.module.scss"
import type { ChatInputProps } from "./types"

export const ChatInput = ({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder = "Напишите сообщение…",
}: ChatInputProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${el.scrollHeight}px`
  }, [value])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!disabled && value.trim()) {
        onSubmit()
      }
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.inputRow}>
        <button className={styles.iconAction} type="button" title="Прикрепить">
          <Plus size={16} />
        </button>

        <textarea
          ref={textareaRef}
          className={styles.textarea}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={disabled}
        />

        <div className={styles.rightActions}>
          <button className={styles.iconAction} type="button" title="Голосовой ввод">
            <Mic size={16} />
          </button>
          <button
            className={styles.sendButton}
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            title="Отправить"
          >
            {disabled ? (
              <Loader2 size={18} className={styles.spinner} />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
      </div>
      <p className={styles.hint}>Enter — отправить · Shift+Enter — новая строка</p>
    </div>
  )
}
