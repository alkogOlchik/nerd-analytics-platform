import styles from "./ProfileScreen.module.scss"
import { Sidebar, UserMenu, ProfileCard } from "modules"
import { useProfile } from "domain/Profile"

export const ProfileScreen = () => {
  const { data: profile, isLoading } = useProfile()

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Профиль</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          <ProfileCard profile={profile} isLoading={isLoading} />
        </div>
      </main>
    </div>
  )
}
