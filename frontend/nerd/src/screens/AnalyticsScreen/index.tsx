import { useState } from "react"
import type { LucideIcon } from "lucide-react"
import { BarChart2, Brain, Shield, Users, Star, FileSearch } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import { OverviewDashboard } from "./dashboards/OverviewDashboard"
import { AiDashboard } from "./dashboards/AiDashboard"
import { AdminsDashboard } from "./dashboards/AdminsDashboard"
import { UsersDashboard } from "./dashboards/UsersDashboard"
import { ReviewsDashboard } from "./dashboards/ReviewsDashboard"
import { TicketsDetailDashboard } from "./dashboards/TicketsDetailDashboard"
import { AnalyticsChatPanel } from "./components/AnalyticsChatPanel"
import { useAnalyticsDashboardContext } from "./hooks/useAnalyticsDashboardContext"
import styles from "./styles.module.scss"

type DashboardId = "overview" | "ai" | "admins" | "users" | "reviews" | "tickets"

interface DashboardTab {
  id: DashboardId
  label: string
  icon: LucideIcon
}

const DASHBOARD_TABS: DashboardTab[] = [
  { id: "overview", label: "Сводная", icon: BarChart2 },
  { id: "ai", label: "ИИ", icon: Brain },
  { id: "admins", label: "Администраторы", icon: Shield },
  { id: "users", label: "Пользователи", icon: Users },
  { id: "reviews", label: "Отзывы", icon: Star },
  { id: "tickets", label: "Тикеты (детально)", icon: FileSearch },
]

const DASHBOARD_MAP: Record<DashboardId, React.FC> = {
  overview: OverviewDashboard,
  ai: AiDashboard,
  admins: AdminsDashboard,
  users: UsersDashboard,
  reviews: ReviewsDashboard,
  tickets: TicketsDetailDashboard,
}

export const AnalyticsScreen = () => {
  const [active, setActive] = useState<DashboardId>("overview")
  const ActiveDashboard = DASHBOARD_MAP[active]
  const dashboardContext = useAnalyticsDashboardContext(active)

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Аналитика</h1>
          <UserMenu />
        </div>

        <div className={styles.tabs}>
          {DASHBOARD_TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`${styles.tab} ${active === id ? styles.tabActive : ""}`}
              onClick={() => setActive(id)}
            >
              <Icon size={15} />
              <span>{label}</span>
            </button>
          ))}
        </div>

        <div className={styles.body}>
          <div className={styles.content}>
            <ActiveDashboard />
          </div>
          <AnalyticsChatPanel context={dashboardContext} />
        </div>
      </main>
    </div>
  )
}
