import styles from "./styles.module.scss"
import type { TicketCardProps } from "./types"
import type { TicketStatus, TicketPriority } from "data/repositories/Tickets"

const STATUS_CONFIG: Record<TicketStatus, { label: string; className: string }> = {
  open: { label: "Открыт", className: styles.statusOpen },
  in_progress: { label: "В обработке", className: styles.statusInProgress },
  closed: { label: "Закрыт", className: styles.statusClosed },
  reopened: { label: "Переоткрыт", className: styles.statusReopened },
}

const PRIORITY_CONFIG: Record<TicketPriority, { label: string; className: string }> = {
  low: { label: "Низкий", className: styles.priorityLow },
  medium: { label: "Средний", className: styles.priorityMedium },
  high: { label: "Высокий", className: styles.priorityHigh },
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" })

export const TicketCard = ({ ticket }: TicketCardProps) => {
  const status = STATUS_CONFIG[ticket.status]
  const priority = PRIORITY_CONFIG[ticket.priority]
  const category = ticket.finalCategory ?? ticket.aiSuggestedCategory
  const subtitle = category ?? (ticket.keywords.length > 0 ? ticket.keywords.join(", ") : null)

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={`${styles.priorityBadge} ${priority.className}`}>{priority.label}</span>
        <span className={`${styles.statusBadge} ${status.className}`}>{status.label}</span>
      </div>

      <h3 className={styles.title}>{ticket.product}</h3>
      {subtitle && <p className={styles.description}>{subtitle}</p>}

      <div className={styles.cardFooter}>
        <span className={styles.date}>{formatDate(ticket.date)}</span>
      </div>
    </div>
  )
}
