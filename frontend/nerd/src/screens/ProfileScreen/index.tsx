import styles from "./ProfileScreen.module.scss"
import { Sidebar } from "modules"

export const ProfileScreen = () => {
    return (
        <div className={styles.page}>
            <Sidebar />
            <main className={styles.main}>
                <h1>Профиль и настройки</h1>
                <p>Страница в разработке</p>
            </main>
        </div>
    )
}
