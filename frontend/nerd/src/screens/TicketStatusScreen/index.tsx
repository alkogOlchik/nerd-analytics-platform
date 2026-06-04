import { ClipboardList } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import styles from "./TicketStatusScreen.module.scss"

export const TicketStatusScreen = () => {
  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Статус обращений</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          <div className={styles.placeholder}>
            <div className={styles.placeholderIcon}>
              <ClipboardList size={36} />
            </div>
            <h2 className={styles.placeholderTitle}>Статус ваших обращений</h2>
            <p className={styles.placeholderSubtitle}>Раздел находится в разработке</p>
          </div>
        </div>
      </main>
    </div>
  )
}
