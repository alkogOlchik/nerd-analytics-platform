import { Clock } from "lucide-react"
import styles from "./styles.module.scss"

interface ComingSoonProps {
  title?: string
  description?: string
}

export const ComingSoon = ({
  title = "Раздел в разработке",
  description = "Данные появятся в следующем обновлении",
}: ComingSoonProps) => (
  <div className={styles.wrapper}>
    <div className={styles.icon}>
      <Clock size={32} />
    </div>
    <h3 className={styles.title}>{title}</h3>
    <p className={styles.desc}>{description}</p>
  </div>
)
