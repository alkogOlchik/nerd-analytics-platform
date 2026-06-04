import { ComingSoon } from "../../components/ComingSoon"
import styles from "./styles.module.scss"

export const UsersDashboard = () => (
  <div className={styles.dashboard}>
    <ComingSoon
      title="Аналитика пользователей"
      description="Статистика прироста пользователей и сводные данные по сегментам появятся после подключения соответствующих эндпоинтов бэкенда."
    />
  </div>
)
