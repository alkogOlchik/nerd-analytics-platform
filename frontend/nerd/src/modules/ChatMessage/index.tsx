import { Bot, User2 } from "lucide-react"
import clsx from "clsx"
import styles from "./styles.module.scss"
import type { ChatMessageProps } from "./types"

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === "user"

  return (
    <div className={clsx(styles.row, isUser ? styles.rowUser : styles.rowAssistant)}>
      {!isUser && (
        <div className={styles.avatar}>
          <Bot size={18} />
        </div>
      )}

      <div className={clsx(styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAssistant)}>
        <p className={styles.content}>{message.content}</p>
      </div>

      {isUser && (
        <div className={clsx(styles.avatar, styles.avatarUser)}>
          <User2 size={18} />
        </div>
      )}
    </div>
  )
}
