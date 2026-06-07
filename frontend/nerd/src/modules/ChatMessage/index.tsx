import { Bot, User2, Download } from "lucide-react"
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
        {!isUser && message.steps && message.steps.length > 0 && (
          <div className={styles.steps}>
            {message.steps.map((step, i) => (
              <span key={i} className={styles.step}>{step}</span>
            ))}
          </div>
        )}
        <p className={styles.content}>{message.content}</p>
        {message.videoUrl && (
          <div className={styles.videoBlock}>
            <video
              className={styles.videoPlayer}
              src={message.videoUrl}
              controls
              preload="metadata"
            />
            <a
              className={styles.videoDownload}
              href={message.videoUrl}
              download
              target="_blank"
              rel="noreferrer"
            >
              <Download size={14} />
              Скачать видео-гайд
            </a>
          </div>
        )}
      </div>

      {isUser && (
        <div className={clsx(styles.avatar, styles.avatarUser)}>
          <User2 size={18} />
        </div>
      )}
    </div>
  )
}
