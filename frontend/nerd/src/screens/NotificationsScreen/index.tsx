import styles from "./NotificationsScreen.module.scss"
import { Sidebar } from "modules"

export const NotificationsScreen = () => {
    return (
        <div className={styles.page}>
            <Sidebar />
            <main className={styles.main}>
                <h1>Уведомления</h1>
                <p>Страница в разработке</p>
            </main>
        </div>
    )
}
