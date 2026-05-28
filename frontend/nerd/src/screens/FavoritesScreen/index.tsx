import styles from "./FavoritesScreen.module.scss"
import { Sidebar } from "modules"

export const FavoritesScreen = () => {
    return (
        <div className={styles.page}>
            <Sidebar />
            <main className={styles.main}>
                <h1>Избранные продукты</h1>
                <p>Страница в разработке</p>
            </main>
        </div>
    )
}
