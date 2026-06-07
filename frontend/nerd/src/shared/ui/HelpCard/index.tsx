import styles from "./styles.module.scss"
import type { HelpCardProps } from "./types"
import GirlImage from "public/girl.png"

export const HelpCard = ({
  title = "Я здесь, чтобы помочь!",
  description = "Сначала я попробую помочь с помощью AI. Если нужно — привлеку специалиста.",
}: HelpCardProps) => {
  return (
    <div className={styles.wrapper}>
      <div className={styles.glow} />
        <div className={styles.avatarCircle}>
          <img src={GirlImage} alt="girl" className={styles.avatarImage} />
        </div>

        <div className={styles.card}>
          <div className={styles.innerGlow} />
          <h3 className={styles.title}>{title}</h3>
          <p className={styles.description}>{description}</p>
        </div>
      </div>

  )
}
