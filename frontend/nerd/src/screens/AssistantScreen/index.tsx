import styles from "./AssistantScreen.module.scss"
import { Sidebar } from "modules"

export const AssistantScreen = () => {
    return (
        <div className={styles.page}>
            <Sidebar />
            <main className={styles.main}>
                <h1>AI-помощник</h1>
                <p>Страница в разработке</p>
            </main>
        </div>
    )
}
