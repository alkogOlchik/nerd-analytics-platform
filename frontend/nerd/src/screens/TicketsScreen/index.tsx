import { useState, type ReactNode } from "react"
import { Loader, CheckCircle, FileText, Clock, Wrench } from "lucide-react"
import styles from "./TicketsScreen.module.scss"
import { Sidebar, UserMenu, TicketCard } from "modules"
import { useTickets } from "domain/Tickets"
import type { TicketStatus } from "data/repositories/Tickets"

type TabValue = "all" | "active" | "waiting" | "processing" | "closed"

const ACTIVE_STATUSES: TicketStatus[] = ["open", "in_progress"]
const CLOSED_STATUSES: TicketStatus[] = ["done", "closed", "reopened"]

const TABS: { value: TabValue; label: string; icon: ReactNode }[] = [
  { value: "all", label: "Все", icon: <FileText size={15} /> },
  { value: "active", label: "В работе", icon: <Loader size={15} /> },
  { value: "waiting", label: "В ожидании оператора", icon: <Clock size={15} /> },
  { value: "processing", label: "Обрабатывается оператором", icon: <Wrench size={15} /> },
  { value: "closed", label: "Закрытые", icon: <CheckCircle size={15} /> },
]

const filterByTab = (tickets: { status: TicketStatus }[], tab: TabValue) => {
  if (tab === "all") return tickets
  if (tab === "active") return tickets.filter((t) => ACTIVE_STATUSES.includes(t.status))
  if (tab === "waiting") return tickets.filter((t) => t.status === "waiting")
  if (tab === "processing") return tickets.filter((t) => t.status === "processing")
  if (tab === "closed") return tickets.filter((t) => CLOSED_STATUSES.includes(t.status))
  return tickets
}

export const TicketsScreen = () => {
  const [activeTab, setActiveTab] = useState<TabValue>("all")
  const { data: tickets = [], isLoading } = useTickets()

  const filteredTickets = filterByTab(tickets, activeTab)

  const countByTab = (tab: TabValue) => filterByTab(tickets, tab).length

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Мои обращения</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
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

          {!isLoading && filteredTickets.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>
                <FileText size={36} />
              </div>
              <h2 className={styles.emptyTitle}>Нет обращений</h2>
              <p className={styles.emptySubtitle}>В этой категории пока нет обращений</p>
            </div>
          )}

          {!isLoading && filteredTickets.length > 0 && (
            <div className={styles.ticketsList}>
              {filteredTickets.map((ticket) => (
                <TicketCard key={ticket.id} ticket={ticket} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
