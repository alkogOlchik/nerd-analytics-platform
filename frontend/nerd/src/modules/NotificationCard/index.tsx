import type { ReactNode } from "react"
import { Bell, MessageSquare, AlertTriangle, Info } from "lucide-react"
import styles from "./styles.module.scss"
import type { NotificationCardProps } from "./types"
import type { NotificationType } from "data/repositories/Notifications"

const TYPE_CONFIG: Record<NotificationType, { icon: ReactNode; className: string }> = {
  ticket_update: {
    icon: <Bell size={16} />,
    className: styles.iconTicketUpdate,
  },
  new_message: {
    icon: <MessageSquare size={16} />,
    className: styles.iconNewMessage,
  },
  system: {
    icon: <AlertTriangle size={16} />,
    className: styles.iconSystem,
  },
  info: {
    icon: <Info size={16} />,
    className: styles.iconInfo,
  },
}

const formatDate = (iso: string) => {
  const date = new Date(iso)
  const now = new Date()
  const isToday =
    date.getDate() === now.getDate() &&
    date.getMonth() === now.getMonth() &&
    date.getFullYear() === now.getFullYear()

  if (isToday) {
    return `сегодня ${date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}`
  }

  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday =
    date.getDate() === yesterday.getDate() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getFullYear() === yesterday.getFullYear()

  if (isYesterday) {
    return `вчера ${date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}`
  }

  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long" })
}

export const NotificationCard = ({ notification, onMarkAsRead }: NotificationCardProps) => {
  const typeConfig = TYPE_CONFIG[notification.type]

  const handleClick = () => {
    if (!notification.isRead) {
      onMarkAsRead(notification.id)
    }
  }

  return (
    <div
      className={`${styles.card} ${notification.isRead ? styles.cardRead : styles.cardUnread}`}
      onClick={handleClick}
      role={!notification.isRead ? "button" : undefined}
      tabIndex={!notification.isRead ? 0 : undefined}
      onKeyDown={(e) => {
        if (!notification.isRead && (e.key === "Enter" || e.key === " ")) {
          onMarkAsRead(notification.id)
        }
      }}
    >
      <div className={`${styles.iconWrap} ${typeConfig.className}`}>{typeConfig.icon}</div>

      <div className={styles.body}>
        <div className={styles.titleRow}>
          <span className={styles.title}>{notification.title}</span>
          {!notification.isRead && <span className={styles.unreadDot} aria-label="Непрочитано" />}
        </div>
        <p className={styles.message}>{notification.message}</p>
      </div>

      <span className={styles.date}>{formatDate(notification.createdAt)}</span>
    </div>
  )
}
