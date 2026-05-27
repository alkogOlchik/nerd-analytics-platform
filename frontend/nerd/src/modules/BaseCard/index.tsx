import clsx from "clsx"

import styles from "./styles.module.scss"

import type { BaseCardProps } from "./types"
import { useBaseCard } from "./useLogic/useBaseCard"

export const BaseCard = ({
  children,
  className,
  hoverable = true,
  onClick,
}: BaseCardProps) => {
  const { clickable, handleClick } = useBaseCard({
    children,
    className,
    hoverable,
    onClick,
  })

  return (
    <div
      onClick={handleClick}
      className={clsx(
        styles.card,
        hoverable && styles.hoverable,
        clickable && styles.clickable,
        className
      )}
    >
      {children}
    </div>
  )
}
