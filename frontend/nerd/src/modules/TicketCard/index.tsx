import styles from "./styles.module.scss"
import type { TicketCardProps } from "./types"
import type { TicketPriority } from "data/repositories/Tickets"

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  in_progress: { label: "В работе", className: styles.statusInProgress },
  waiting_for_operator: { label: "Ожидание оператора", className: styles.statusWaiting },
  in_operator_processing: { label: "У оператора", className: styles.statusOperator },
  closed: { label: "Закрыт", className: styles.statusClosed },
  open: { label: "Открыт", className: styles.statusOpen },
  reopened: { label: "Переоткрыт", className: styles.statusReopened },
  // legacy Russian
  "принято": { label: "Принято", className: styles.statusOpen },
  "в_работе": { label: "В работе", className: styles.statusInProgress },
  "закрыто": { label: "Закрыт", className: styles.statusClosed },
}

const PRIORITY_CONFIG: Record<TicketPriority, { label: string; className: string }> = {
  low: { label: "Низкий", className: styles.priorityLow },
  medium: { label: "Средний", className: styles.priorityMedium },
  high: { label: "Высокий", className: styles.priorityHigh },
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" })

export const TicketCard = ({ ticket }: TicketCardProps) => {
  const status = STATUS_CONFIG[ticket.status] ?? { label: ticket.status, className: styles.statusInProgress }
  const priority = PRIORITY_CONFIG[ticket.priority]
  const category = ticket.finalCategory ?? ticket.aiSuggestedCategory
  const subtitle = category ?? (ticket.keywords.length > 0 ? ticket.keywords.join(", ") : null)
  const displayTitle = ticket.title ?? ticket.product ?? "Обращение"

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={`${styles.priorityBadge} ${priority.className}`}>{priority.label}</span>
        <span className={`${styles.statusBadge} ${status.className}`}>{status.label}</span>
      </div>

      <h3 className={styles.title}>{displayTitle}</h3>
      {subtitle && <p className={styles.description}>{subtitle}</p>}

      <div className={styles.cardFooter}>
        <span className={styles.date}>{formatDate(ticket.date)}</span>
      </div>
    </div>
  )
}
