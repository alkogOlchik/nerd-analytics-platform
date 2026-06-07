import { Send, Mic, Plus } from "lucide-react"
import styles from "./styles.module.scss"
import type { PromptCardProps } from "./types"

export const PromptCard = ({ value, onChange, onSubmit }: PromptCardProps) => {
  return (
    <div className={styles.card}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            onSubmit()
          }
        }}
        placeholder="Опишите вашу проблему..."
        className={styles.textarea}
      />

      <div className={styles.footer}>
        <button className={styles.iconButton}>
          <Plus size={20} />
        </button>

        <div className={styles.actions}>
          <button className={styles.iconButton}>
            <Mic size={20} />
          </button>

          <button onClick={onSubmit} className={styles.submitButton}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}
