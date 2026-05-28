import { Link } from "react-router-dom"
import { routes } from "../../shared/utils/routes"
import styles from "./NotFoundScreen.module.scss"

export const NotFoundScreen = () => {
    return (
        <div className={styles.container}>
            <h1>404</h1>
            <p>Запрашиваемая страница не существует или была перемещена.</p>
            <Link to={routes.main} className={styles.link}>
                Вернуться на главную
            </Link>
        </div>
    )
}
