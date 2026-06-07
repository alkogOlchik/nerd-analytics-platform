import { Link } from "react-router-dom"
import { useParams } from "react-router-dom"
import { ClipboardList, AlertCircle } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import { useGuestTicketTrack } from "domain/Tickets"
import { routes } from "shared/utils/routes"
import styles from "./GuestTicketTrackScreen.module.scss"

const STATUS_LABELS: Record<string, string> = {
  open: "Открыт",
  in_progress: "В обработке",
  closed: "Закрыт",
  reopened: "Переоткрыт",
  waiting_for_operator: "Ожидает оператора",
  in_operator_processing: "Обрабатывается оператором",
}

const STATUS_CLASSES: Record<string, string> = {
  open: styles.statusOpen,
  in_progress: styles.statusInProgress,
  closed: styles.statusClosed,
  reopened: styles.statusReopened,
  waiting_for_operator: styles.statusWaiting,
  in_operator_processing: styles.statusInProgress,
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" })

export const GuestTicketTrackScreen = () => {
  const { token } = useParams<{ token: string }>()
  const { data: ticket, isLoading, isError } = useGuestTicketTrack(token)

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Статус обращения</h1>
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

          {isError && (
            <div className={styles.errorState}>
              <div className={styles.errorIcon}>
                <AlertCircle size={32} />
              </div>
              <h2 className={styles.errorTitle}>Обращение не найдено</h2>
              <p className={styles.errorText}>
                Ссылка недействительна или срок её действия истёк.
              </p>
              <Link to={routes.createTicket} className={styles.actionBtn}>
                Создать новое обращение
              </Link>
            </div>
          )}

          {ticket && (
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <div className={styles.iconWrap}>
                  <ClipboardList size={24} />
                </div>
                <div>
                  <p className={styles.cardProduct}>{ticket.product}</p>
                  <p className={styles.cardDate}>Создано {formatDate(ticket.createdAt)}</p>
                </div>
                <span className={`${styles.statusBadge} ${STATUS_CLASSES[ticket.status] ?? styles.statusOpen}`}>
                  {STATUS_LABELS[ticket.status] ?? ticket.status}
                </span>
              </div>

              {ticket.statusUpdatedAt && (
                <p className={styles.updatedAt}>
                  Статус обновлён: {formatDate(ticket.statusUpdatedAt)}
                </p>
              )}

              <div className={styles.registerPrompt}>
                <p className={styles.registerPromptText}>
                  Зарегистрируйтесь, чтобы управлять обращениями и получать уведомления в личном кабинете.
                </p>
                <div className={styles.registerPromptActions}>
                  <Link to={routes.register} className={styles.actionBtn}>
                    Зарегистрироваться
                  </Link>
                  <Link to={routes.login} className={styles.actionBtnSecondary}>
                    Войти
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
