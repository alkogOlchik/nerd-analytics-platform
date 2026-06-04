import { Lightbulb } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import styles from "./FeedbackScreen.module.scss"

export const FeedbackScreen = () => {
  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Написать отзыв</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          <div className={styles.placeholder}>
            <div className={styles.placeholderIcon}>
              <Lightbulb size={36} />
            </div>
            <h2 className={styles.placeholderTitle}>Форма отзыва</h2>
            <p className={styles.placeholderSubtitle}>Раздел находится в разработке</p>
          </div>
        </div>
      </main>
    </div>
  )
}
