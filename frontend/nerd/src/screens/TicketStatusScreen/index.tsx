import { useState } from "react"
import { ClipboardList } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import { useTickets, useReopenTicket } from "domain/Tickets"
import { useCreateReview } from "domain/Reviews/useCreateReview"
import type { Ticket, TicketStatus, TicketPriority } from "data/repositories/Tickets"
import styles from "./TicketStatusScreen.module.scss"

const STATUS_CONFIG: Record<TicketStatus, { label: string; cls: string }> = {
  open: { label: "Открыт", cls: styles.statusOpen },
  in_progress: { label: "В обработке", cls: styles.statusInProgress },
  closed: { label: "Закрыт", cls: styles.statusClosed },
  reopened: { label: "Переоткрыт", cls: styles.statusReopened },
}

const PRIORITY_CONFIG: Record<TicketPriority, { label: string; cls: string }> = {
  low: { label: "Низкий", cls: styles.priorityLow },
  medium: { label: "Средний", cls: styles.priorityMedium },
  high: { label: "Высокий", cls: styles.priorityHigh },
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long" })

interface RateState {
  ticketId: string
  product: string
}

const RatingModal = ({
  ticketId,
  product,
  onClose,
}: {
  ticketId: string
  product: string
  onClose: () => void
}) => {
  const [rating, setRating] = useState(0)
  const [hover, setHover] = useState(0)
  const [comment, setComment] = useState("")
  const { mutateAsync: createReview, isPending } = useCreateReview()

  const handleSubmit = async () => {
    if (!rating) return
    await createReview({ ticketId, product, rating, comment: comment || undefined })
    onClose()
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.modalTitle}>Оценить обращение</h2>
        <div>
          <p className={styles.modalLabel}>Оценка *</p>
          <div className={styles.stars}>
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                className={`${styles.star} ${n <= (hover || rating) ? styles.starActive : ""}`}
                onMouseEnter={() => setHover(n)}
                onMouseLeave={() => setHover(0)}
                onClick={() => setRating(n)}
              >
                ★
              </button>
            ))}
          </div>
        </div>
        <textarea
          className={styles.modalTextarea}
          placeholder="Оставьте комментарий (необязательно)"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        <div className={styles.modalActions}>
          <button className={styles.cancelBtn} onClick={onClose}>
            Отмена
          </button>
          <button
            className={styles.submitBtn}
            disabled={!rating || isPending}
            onClick={handleSubmit}
          >
            {isPending ? "Отправляем..." : "Отправить"}
          </button>
        </div>
      </div>
    </div>
  )
}

export const TicketStatusScreen = () => {
  const { data: tickets = [], isLoading } = useTickets()
  const { mutate: reopen, isPending: isReopening } = useReopenTicket()
  const [rateState, setRateState] = useState<RateState | null>(null)

  const grouped = tickets.reduce<Record<string, Ticket[]>>((acc, t) => {
    ;(acc[t.product] ??= []).push(t)
    return acc
  }, {})

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Статус обращений</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          {isLoading && (
            <div className={styles.loading}>
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
            </div>
          )}

          {!isLoading && tickets.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>
                <ClipboardList size={36} />
              </div>
              <h2 className={styles.emptyTitle}>Нет обращений</h2>
              <p className={styles.emptySubtitle}>Вы ещё не создавали обращений</p>
            </div>
          )}

          {!isLoading &&
            Object.entries(grouped).map(([product, items]) => (
              <div key={product} className={styles.group}>
                <h2 className={styles.groupTitle}>{product}</h2>
                <div className={styles.ticketsList}>
                  {items.map((t) => {
                    const st = STATUS_CONFIG[t.status]
                    const pr = PRIORITY_CONFIG[t.priority]
                    const category = t.finalCategory ?? t.aiSuggestedCategory
                    return (
                      <div key={t.id} className={styles.ticket}>
                        <div className={styles.ticketHeader}>
                          <span className={`${styles.statusBadge} ${st.cls}`}>{st.label}</span>
                          <span className={`${styles.priorityBadge} ${pr.cls}`}>{pr.label}</span>
                        </div>
                        {category && <p className={styles.ticketCategory}>{category}</p>}
                        <div className={styles.ticketFooter}>
                          <span className={styles.ticketDate}>{formatDate(t.date)}</span>
                          <div className={styles.ticketActions}>
                            {t.status === "closed" && (
                              <button
                                className={styles.actionBtn}
                                onClick={() => setRateState({ ticketId: t.id, product: t.product })}
                              >
                                Оценить
                              </button>
                            )}
                            {(t.status === "closed" || t.status === "open") && (
                              <button
                                className={`${styles.actionBtn} ${styles.reopenBtn}`}
                                disabled={isReopening}
                                onClick={() => reopen(t.id)}
                              >
                                Переоткрыть
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
        </div>
      </main>

      {rateState && (
        <RatingModal
          ticketId={rateState.ticketId}
          product={rateState.product}
          onClose={() => setRateState(null)}
        />
      )}
    </div>
  )
}
