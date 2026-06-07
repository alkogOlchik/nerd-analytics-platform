import type { LucideIcon } from "lucide-react"

export interface QuickActionCardProps {
  title: string
  description: string
  icon: LucideIcon
  onClick?: () => void
}
