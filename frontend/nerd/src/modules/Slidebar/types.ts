import type { LucideIcon } from "lucide-react"

export interface SidebarItem {
  id: string
  label: string
  icon: LucideIcon
  active?: boolean
  notifications?: number
}

export interface SidebarProps {
  onSelect: (id: string) => void
}
