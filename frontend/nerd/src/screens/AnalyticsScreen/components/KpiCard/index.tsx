import styles from "./styles.module.scss"
import clsx from "clsx"

interface KpiCardProps {
  label: string
  value: string | number
  unit?: string
  highlight?: "success" | "warning" | "danger"
  placeholder?: boolean
}

export const KpiCard = ({ label, value, unit, highlight, placeholder }: KpiCardProps) => (
  <div className={clsx(styles.card, highlight && styles[highlight], placeholder && styles.placeholder)}>
    <span className={styles.label}>{label}</span>
    <div className={styles.valueRow}>
      <span className={styles.value}>{placeholder ? "—" : value}</span>
      {unit && !placeholder && <span className={styles.unit}>{unit}</span>}
    </div>
  </div>
)
