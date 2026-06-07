import { MessageSquare, Plus } from "lucide-react"
import clsx from "clsx"
import styles from "./styles.module.scss"
import type { ChatHistoryProps } from "./types"
import { useChatHistory } from "./useLogic/useChatHistory"
import { HISTORY_TITLE, NEW_CHAT_LABEL } from "./constants"

const STATUS_LABEL: Record<string, string> = {
  in_progress: "в работе",
  waiting_for_operator: "ожидание",
  in_operator_processing: "у оператора",
  closed: "закрыт",
}

const STATUS_CLASS: Record<string, string> = {
  in_progress: styles.statusInProgress,
  waiting_for_operator: styles.statusWaiting,
  in_operator_processing: styles.statusOperator,
  closed: styles.statusClosed,
}

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
          sessions.map((session) => {
            const statusLabel = session.ticketStatus ? STATUS_LABEL[session.ticketStatus] : undefined
            const statusClass = session.ticketStatus ? STATUS_CLASS[session.ticketStatus] : undefined

            return (
              <button
                key={session.id}
                className={clsx(
                  styles.item,
                  session.id === activeSessionId && styles.itemActive,
                )}
                onClick={() => handleSelect(session.id)}
              >
                <MessageSquare size={16} className={styles.itemIcon} />
                <div className={styles.itemContent}>
                  <div className={styles.itemTitleRow}>
                    <span className={styles.itemTitle}>{session.title}</span>
                    {statusLabel && statusClass && (
                      <span className={clsx(styles.itemStatus, statusClass)}>{statusLabel}</span>
                    )}
                  </div>
                  {session.lastMessage && (
                    <span className={styles.itemPreview}>{session.lastMessage}</span>
                  )}
                </div>
              </button>
            )
          })}
      </div>
    </aside>
  )
}
