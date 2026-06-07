import { useState, type ReactNode } from "react"
import { Circle, Loader, CheckCircle, RotateCcw, FileText } from "lucide-react"
import styles from "./TicketsScreen.module.scss"
import { Sidebar, UserMenu, TicketCard } from "modules"
import { useTickets, useUpdateTicketStatus } from "domain/Tickets"
import { useMe } from "domain/Auth/useMe"
import type { Ticket, TicketStatus } from "data/repositories/Tickets"

type TabValue = "all" | TicketStatus

const TABS: { value: TabValue; label: string; icon: ReactNode }[] = [
  { value: "all", label: "Все", icon: <FileText size={15} /> },
  { value: "open", label: "Открытые", icon: <Circle size={15} /> },
  { value: "in_progress", label: "В обработке", icon: <Loader size={15} /> },
  { value: "closed", label: "Закрытые", icon: <CheckCircle size={15} /> },
  { value: "reopened", label: "Переоткрытые", icon: <RotateCcw size={15} /> },
]

const PRODUCTS = [
  "веб-сервис",
  "платёжный сервис",
  "мобильное приложение",
  "API интеграция",
  "личный кабинет",
  "аналитический модуль",
]

const STATUS_LABELS: Record<TicketStatus, string> = {
  open: "Открыт",
  in_progress: "В обработке",
  closed: "Закрыт",
  reopened: "Переоткрыт",
}

const STATUS_BADGE: Record<TicketStatus, string> = {
  open: styles.statusOpen,
  in_progress: styles.statusInProgress,
  closed: styles.statusClosed,
  reopened: styles.statusReopened,
}

const PRIORITY_LABELS: Record<string, string> = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
}

const PRIORITY_BADGE: Record<string, string> = {
  low: styles.priorityLow,
  medium: styles.priorityMedium,
  high: styles.priorityHigh,
}

const NEXT_STATUSES: TicketStatus[] = ["open", "in_progress", "closed"]

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "short" })

const AdminTicketRow = ({ ticket }: { ticket: Ticket }) => {
  const { mutate: patchStatus, isPending } = useUpdateTicketStatus()
  const [selectedStatus, setSelectedStatus] = useState<TicketStatus>(ticket.status)

  const handleStatusChange = (status: TicketStatus) => {
    setSelectedStatus(status)
    patchStatus({ id: ticket.id, status })
  }

  const category = ticket.finalCategory ?? ticket.aiSuggestedCategory

  return (
    <div className={styles.ticketRow}>
      <div className={styles.rowTop}>
        <span className={styles.ticketProduct}>{ticket.product}</span>
        <span className={`${styles.badge} ${STATUS_BADGE[selectedStatus]}`}>
          {STATUS_LABELS[selectedStatus]}
        </span>
        <span className={`${styles.badge} ${PRIORITY_BADGE[ticket.priority]}`}>
          {PRIORITY_LABELS[ticket.priority] ?? ticket.priority}
        </span>
      </div>

      <div className={styles.rowMeta}>
        {category && <span className={styles.metaText}>{category}</span>}
        <span className={styles.metaText}>{formatDate(ticket.date)}</span>
        {ticket.deadline && (
          <span className={styles.metaText}>дедлайн: {formatDate(ticket.deadline)}</span>
        )}
      </div>

      <div className={styles.rowActions}>
        <select
          className={styles.actionSelect}
          value={selectedStatus}
          disabled={isPending}
          onChange={(e) => handleStatusChange(e.target.value as TicketStatus)}
        >
          {NEXT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

export const TicketsScreen = () => {
  const [activeTab, setActiveTab] = useState<TabValue>("all")
  const [search, setSearch] = useState("")
  const [filterProduct, setFilterProduct] = useState("")
  const [filterPriority, setFilterPriority] = useState("")

  const { data: user } = useMe()
  const isAdmin = user?.role === "employee"

  const { data: tickets = [], isLoading } = useTickets()

  const filtered = tickets.filter((t) => {
    if (activeTab !== "all" && t.status !== activeTab) return false
    if (filterProduct && t.product !== filterProduct) return false
    if (filterPriority && t.priority !== filterPriority) return false
    if (search) {
      const q = search.toLowerCase()
      const haystack = [
        t.product,
        t.finalCategory,
        t.aiSuggestedCategory,
        ...(t.keywords ?? []),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      if (!haystack.includes(q)) return false
    }
    return true
  })

  const countByTab = (tab: TabValue) =>
    tab === "all" ? tickets.length : tickets.filter((t) => t.status === tab).length

  const hasFilters = search || filterProduct || filterPriority

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>{isAdmin ? "Все обращения" : "Мои обращения"}</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          {isAdmin && (
            <div className={styles.toolbar}>
              <input
                className={styles.searchInput}
                type="text"
                placeholder="Поиск по продукту, категории..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />

              <select
                className={styles.filterSelect}
                value={filterProduct}
                onChange={(e) => setFilterProduct(e.target.value)}
              >
                <option value="">Все продукты</option>
                {PRODUCTS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>

              <select
                className={styles.filterSelect}
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
              >
                <option value="">Все приоритеты</option>
                {Object.entries(PRIORITY_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>

              {hasFilters && (
                <button
                  className={styles.resetBtn}
                  onClick={() => { setSearch(""); setFilterProduct(""); setFilterPriority("") }}
                >
                  Сбросить
                </button>
              )}
            </div>
          )}

          <div className={styles.tabs}>
            {TABS.map(({ value, label, icon }) => (
              <button
                key={value}
                className={`${styles.tab} ${activeTab === value ? styles.tabActive : ""}`}
                onClick={() => setActiveTab(value)}
              >
                {icon}
                <span>{label}</span>
                {!isLoading && (
                  <span className={styles.tabCount}>{countByTab(value)}</span>
                )}
              </button>
            ))}
          </div>

          {isLoading && (
            <div className={styles.loading}>
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
            </div>
          )}

          {!isLoading && filtered.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>
                <FileText size={36} />
              </div>
              <h2 className={styles.emptyTitle}>Нет обращений</h2>
              <p className={styles.emptySubtitle}>В этой категории пока нет обращений</p>
            </div>
          )}

          {!isLoading && filtered.length > 0 && (
            <div className={styles.ticketsList}>
              {filtered.map((ticket) =>
                isAdmin ? (
                  <AdminTicketRow key={ticket.id} ticket={ticket} />
                ) : (
                  <TicketCard key={ticket.id} ticket={ticket} />
                )
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
