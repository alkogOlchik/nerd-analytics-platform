import { useState } from "react"
import { BellOff } from "lucide-react"
import styles from "./NotificationsScreen.module.scss"
import { Sidebar, UserMenu, NotificationCard } from "modules"
import { useNotifications, useMarkAsRead, useMarkAllAsRead } from "domain/Notifications"

type Filter = "all" | "unread" | "read"

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "Все" },
  { value: "unread", label: "Непрочитанные" },
  { value: "read", label: "Прочитанные" },
]

export const NotificationsScreen = () => {
  const [filter, setFilter] = useState<Filter>("all")

  const { data: notifications = [], isLoading } = useNotifications()
  const { mutate: markAsRead } = useMarkAsRead()
  const { mutate: markAllAsRead, isPending: isMarkingAll } = useMarkAllAsRead()

  const unreadCount = notifications.filter((n) => !n.isRead).length
  const readCount = notifications.filter((n) => n.isRead).length

  const countByFilter = (f: Filter) => {
    if (f === "all") return notifications.length
    if (f === "unread") return unreadCount
    return readCount
  }

  const filteredNotifications = notifications.filter((n) => {
    if (filter === "unread") return !n.isRead
    if (filter === "read") return n.isRead
    return true
  })

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Уведомления</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          <div className={styles.toolbar}>
            <div className={styles.tabs}>
              {FILTERS.map(({ value, label }) => (
                <button
                  key={value}
                  className={`${styles.tab} ${filter === value ? styles.tabActive : ""}`}
                  onClick={() => setFilter(value)}
                >
                  <span>{label}</span>
                  {!isLoading && (
                    <span className={styles.tabCount}>{countByFilter(value)}</span>
                  )}
                </button>
              ))}
            </div>

            {unreadCount > 0 && !isLoading && (
              <button
                className={styles.markAllBtn}
                onClick={() => markAllAsRead()}
                disabled={isMarkingAll}
              >
                {isMarkingAll ? "Отмечаем..." : "Отметить все прочитанными"}
              </button>
            )}
          </div>

          {isLoading && (
            <div className={styles.loading}>
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
            </div>
          )}

          {!isLoading && filteredNotifications.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>
                <BellOff size={36} />
              </div>
              <h2 className={styles.emptyTitle}>Нет уведомлений</h2>
              <p className={styles.emptySubtitle}>
                {filter === "unread"
                  ? "Все уведомления прочитаны"
                  : "В этой категории пока нет уведомлений"}
              </p>
            </div>
          )}

          {!isLoading && filteredNotifications.length > 0 && (
            <div className={styles.list}>
              {filteredNotifications.map((notification) => (
                <NotificationCard
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={markAsRead}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
