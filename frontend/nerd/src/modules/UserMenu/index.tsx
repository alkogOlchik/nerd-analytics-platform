import { User2, LogOut, Settings, User } from "lucide-react"
import { Link } from "react-router-dom"
import { routes } from "shared/utils/routes"
import { useUserMenu } from "./useLogic/useUserMenu"
import type { UserMenuProps } from "./types"
import styles from "./styles.module.scss"

export const UserMenu = ({ className }: UserMenuProps) => {
  const { user, isLoading, isOpen, isLoggingOut, displayName, toggle, handleLogout } = useUserMenu()

  if (!isLoading && !user) {
    return (
      <div className={`${styles.wrapper}${className ? ` ${className}` : ""}`}>
        <Link to={routes.login} className={styles.loginButton}>
          Войти
        </Link>
      </div>
    )
  }

  return (
    <div className={`${styles.wrapper}${className ? ` ${className}` : ""}`}>
      <p className={styles.greeting}>Привет, {displayName}</p>

      <div className={styles.avatar} onClick={toggle} role="button" tabIndex={0}>
        <User2 size={30} />

        {isOpen && (
          <div className={styles.dropdown}>
            <div className={styles.dropdownHeader}>
              <div className={styles.avatarLarge}>
                <User2 size={40} />
              </div>
              <div>
                <p className={styles.fullName}>{user?.fullName ?? user?.username}</p>
                {user?.email && <p className={styles.email}>{user.email}</p>}
              </div>
            </div>

            <div className={styles.divider} />

            <Link to={routes.profile} className={styles.link}>
              <User size={18} />
              <span>Профиль</span>
            </Link>

            <Link to={routes.profile} className={styles.link}>
              <Settings size={18} />
              <span>Настройки</span>
            </Link>

            <div className={styles.divider} />

            <button
              className={styles.logoutButton}
              onClick={handleLogout}
              disabled={isLoggingOut}
            >
              <LogOut size={18} />
              <span>{isLoggingOut ? "Выходим..." : "Выйти"}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
