import styles from "./SettingsScreen.module.scss"
import { Sidebar, UserMenu, EditProfileForm, ChangePasswordForm } from "modules"
import { useProfile } from "domain/Profile"

export const SettingsScreen = () => {
  const { data: profile, isLoading: isProfileLoading } = useProfile()

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Настройки</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          <EditProfileForm profile={profile} isProfileLoading={isProfileLoading} />
          <ChangePasswordForm />
        </div>
      </main>
    </div>
  )
}
