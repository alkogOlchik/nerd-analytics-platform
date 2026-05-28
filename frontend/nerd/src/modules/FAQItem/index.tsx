import { ChevronRight } from "lucide-react"

import styles from "./styles.module.scss"

import type { FAQItemProps } from "./types"

export const FAQItem = ({ question, category, onClick }: FAQItemProps) => {
  return (
    <button onClick={onClick} className={styles.item}>
      <span className={styles.question}>{question}</span>

      <div className={styles.right}>
        <span className={styles.category}>{category}</span>

        <ChevronRight className={styles.icon} />
      </div>
    </button>
  )
}
