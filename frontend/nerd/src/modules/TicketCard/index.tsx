import type { ReactNode } from "react"
import { AlertTriangle, HelpCircle, Star } from "lucide-react"
import styles from "./styles.module.scss"
import type { TicketCardProps } from "./types"
import type { TicketCategory, TicketStatus } from "data/repositories/Tickets"

const CATEGORY_CONFIG: Record<TicketCategory, { label: string; icon: ReactNode; className: string }> = {
  complaint: {
    label: "Жалоба",
    icon: <AlertTriangle size={13} />,
    className: styles.categoryComplaint,
  },
  support: {
    label: "Помощь",
    icon: <HelpCircle size={13} />,
    className: styles.categorySupport,
  },
  review: {
    label: "Отзыв",
    icon: <Star size={13} />,
    className: styles.categoryReview,
  },
}

const STATUS_CONFIG: Record<TicketStatus, { label: string; className: string }> = {
  open: { label: "Открыт", className: styles.statusOpen },
  in_progress: { label: "В обработке", className: styles.statusInProgress },
  closed: { label: "Закрыт", className: styles.statusClosed },
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" })

export const TicketCard = ({ ticket }: TicketCardProps) => {
  const category = CATEGORY_CONFIG[ticket.category]
  const status = STATUS_CONFIG[ticket.status]

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={`${styles.categoryBadge} ${category.className}`}>
          {category.icon}
          {category.label}
        </span>
        <span className={`${styles.statusBadge} ${status.className}`}>{status.label}</span>
      </div>

      <h3 className={styles.title}>{ticket.title}</h3>
      <p className={styles.description}>{ticket.description}</p>

      <div className={styles.cardFooter}>
        <span className={styles.date}>{formatDate(ticket.createdAt)}</span>
      </div>
    </div>
  )
}
