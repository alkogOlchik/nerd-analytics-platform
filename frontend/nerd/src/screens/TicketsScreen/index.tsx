import styles from "./TicketsScreen.module.scss"
import { Sidebar } from "modules"

export const TicketsScreen = () => {
    return (
        <div className={styles.page}>
            <Sidebar />
            <main className={styles.main}>
                <h1>Мои обращения</h1>
                <p>Страница в разработке</p>
            </main>
        </div>
    )
}
