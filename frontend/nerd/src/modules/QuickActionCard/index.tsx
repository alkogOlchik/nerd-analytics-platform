import styles from "./styles.module.scss"

import type { QuickActionCardProps } from "./types"

import { BaseCard } from "../BaseCard"
import { LiquidWrapper } from "shared/ui/LiquidWrapper"

export const QuickActionCard = ({
  title,
  description,
  icon: Icon,
  onClick,
}: QuickActionCardProps) => {
  return (
    <LiquidWrapper onClick={onClick} alwaysActive className={styles.wrapper}>
      <BaseCard className={styles.card}>
        <div className={styles.iconWrapper}>
          <Icon size={28} />
        </div>

        <div className={styles.content}>
          <h3 className={styles.title}>{title}</h3>

          <p className={styles.description}>{description}</p>
        </div>
      </BaseCard>
    </LiquidWrapper>
  )
}
