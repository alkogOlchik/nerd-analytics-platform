import type { ButtonHTMLAttributes, ReactNode } from "react"

export interface LiquidWrapperProps extends ButtonHTMLAttributes<HTMLDivElement> {
  children: ReactNode
  className?: string
  isActive?: boolean
  alwaysActive?: boolean
}
