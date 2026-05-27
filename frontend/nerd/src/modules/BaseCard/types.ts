import type { ReactNode } from "react"

export interface BaseCardProps {
  children: ReactNode
  className?: string
  hoverable?: boolean
  onClick?: () => void
}
