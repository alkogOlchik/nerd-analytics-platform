import { Home, Bot, Bell, Star, User, FileText } from "lucide-react"
import type { SidebarItem } from "./types"

export const NAVIGATION_ITEMS: SidebarItem[] = [
  {
    id: "home",
    label: "Главная",
    icon: Home,
    active: true,
  },
  {
    id: "assistant",
    label: "AI-помощник",
    icon: Bot,
  },
  {
    id: "tickets",
    label: "Мои обращения",
    icon: FileText,
  },
  {
    id: "favorites",
    label: "Избранные продукты",
    icon: Star,
  },
  {
    id: "notifications",
    label: "Уведомления",
    icon: Bell,
    notifications: 3,
  },
  {
    id: "profile",
    label: "Профиль и настройки",
    icon: User,
  },
]
