import { MessageSquare, Plus } from "lucide-react"
import clsx from "clsx"
import styles from "./styles.module.scss"
import type { ChatHistoryProps } from "./types"
import { useChatHistory } from "./useLogic/useChatHistory"
import { HISTORY_TITLE, NEW_CHAT_LABEL } from "./constants"

export const ChatHistory = ({
  sessions,
  activeSessionId,
  isLoading,
  onSelect,
  onNewChat,
}: ChatHistoryProps) => {
  const { handleSelect, handleNewChat } = useChatHistory({ onSelect, onNewChat })

  return (
    <aside className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.title}>{HISTORY_TITLE}</span>
        <button
          className={styles.newChatButton}
          onClick={handleNewChat}
          title={NEW_CHAT_LABEL}
        >
          <Plus size={18} />
        </button>
      </div>

      <div className={styles.list}>
        {isLoading && (
          <div className={styles.loading}>
            <span className={styles.loadingDot} />
            <span className={styles.loadingDot} />
            <span className={styles.loadingDot} />
          </div>
        )}

        {!isLoading && sessions.length === 0 && (
          <p className={styles.empty}>Нет чатов</p>
        )}

        {!isLoading &&
          sessions.map((session) => (
            <button
              key={session.id}
              className={clsx(
                styles.item,
                session.id === activeSessionId && styles.itemActive
              )}
              onClick={() => handleSelect(session.id)}
            >
              <MessageSquare size={16} className={styles.itemIcon} />
              <div className={styles.itemContent}>
                <span className={styles.itemTitle}>{session.title}</span>
                {session.lastMessage && (
                  <span className={styles.itemPreview}>{session.lastMessage}</span>
                )}
              </div>
            </button>
          ))}
      </div>
    </aside>
  )
}
