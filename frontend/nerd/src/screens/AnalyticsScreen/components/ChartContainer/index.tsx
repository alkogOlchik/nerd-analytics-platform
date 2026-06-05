import type { ReactNode, RefObject } from "react"
import styles from "./styles.module.scss"

interface ChartContainerProps {
  title: string
  isLoading: boolean
  error?: Error | null
  children: ReactNode
  containerRef?: RefObject<HTMLDivElement | null>
  minHeight?: number
  wide?: boolean
}

export const ChartContainer = ({
  title,
  isLoading,
  error,
  children,
  containerRef,
  minHeight = 280,
  wide,
}: ChartContainerProps) => (
  <div className={`${styles.card}${wide ? ` ${styles.cardWide}` : ""}`}>
    <h3 className={styles.title}>{title}</h3>
    <div className={styles.body} style={{ minHeight }} ref={containerRef}>
      {isLoading && (
        <div className={styles.loading}>
          <span className={styles.dot} />
          <span className={styles.dot} />
          <span className={styles.dot} />
        </div>
      )}
      {!isLoading && error && (
        <div className={styles.error}>Ошибка загрузки данных</div>
      )}
      {!isLoading && !error && children}
    </div>
  </div>
)
