import { useState, type ReactNode } from "react"
import { AlertTriangle, HelpCircle, Star, FileText } from "lucide-react"
import styles from "./TicketsScreen.module.scss"
import { Sidebar, UserMenu, TicketCard } from "modules"
import { useTickets } from "domain/Tickets"
import type { TicketCategory } from "data/repositories/Tickets"

const TABS: { category: TicketCategory; label: string; icon: ReactNode }[] = [
  { category: "complaint", label: "Жалобы", icon: <AlertTriangle size={15} /> },
  { category: "support", label: "Помощь", icon: <HelpCircle size={15} /> },
  { category: "review", label: "Отзывы", icon: <Star size={15} /> },
]

export const TicketsScreen = () => {
  const [activeCategory, setActiveCategory] = useState<TicketCategory>("complaint")
  const { data: tickets = [], isLoading } = useTickets()

  const filteredTickets = tickets.filter((t) => t.category === activeCategory)
  const countByCategory = (cat: TicketCategory) => tickets.filter((t) => t.category === cat).length

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
            {TABS.map(({ category, label, icon }) => (
              <button
                key={category}
                className={`${styles.tab} ${activeCategory === category ? styles.tabActive : ""}`}
                onClick={() => setActiveCategory(category)}
              >
                {icon}
                <span>{label}</span>
                {!isLoading && (
                  <span className={styles.tabCount}>{countByCategory(category)}</span>
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
