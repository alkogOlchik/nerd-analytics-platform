import type { LucideIcon } from "lucide-react"

export interface SidebarItem {
  id: string
  label: string
  icon: LucideIcon
  path: string
  active?: boolean
  notifications?: number
}

export interface SidebarProps {
  onSelect?: (id: string) => void
}
