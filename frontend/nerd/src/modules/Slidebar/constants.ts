import { Home, Bot, Bell, FileText, BarChart2 } from "lucide-react"
import type { SidebarItem } from "./types"
import { routes } from "shared/utils/routes"

export const NAVIGATION_ITEMS: SidebarItem[] = [
  {
    id: "home",
    label: "Главная",
    icon: Home,
    path: routes.main,
    active: true,
  },
  {
    id: "assistant",
    label: "AI-помощник",
    icon: Bot,
    path: routes.assistant,
  },
  {
    id: "tickets",
    label: "Мои обращения",
    icon: FileText,
    path: routes.tickets,
  },
  {
    id: "analytics",
    label: "Аналитика",
    icon: BarChart2,
    path: routes.analytics,
  },
  {
    id: "notifications",
    label: "Уведомления",
    icon: Bell,
    path: routes.notifications,
    notifications: 3,
  },
]
