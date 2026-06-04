import { AlertTriangle } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import styles from "./CreateTicketScreen.module.scss"

export const CreateTicketScreen = () => {
  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Создать обращение</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          <div className={styles.placeholder}>
            <div className={styles.placeholderIcon}>
              <AlertTriangle size={36} />
            </div>
            <h2 className={styles.placeholderTitle}>Форма создания обращения</h2>
            <p className={styles.placeholderSubtitle}>Раздел находится в разработке</p>
          </div>
        </div>
      </main>
    </div>
  )
}
