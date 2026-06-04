import { User2, LogOut, Settings, User } from "lucide-react"
import { Link } from "react-router-dom"
import { authRepository } from "data/repositories/Auth"
import { routes } from "shared/utils/routes"
import { useUserMenu } from "./useLogic/useUserMenu"
import type { UserMenuProps } from "./types"
import styles from "./styles.module.scss"

export const UserMenu = ({ className }: UserMenuProps) => {
  const { profile, isLoading, isOpen, displayName, toggle, handleLogout } = useUserMenu()

  if (!authRepository.hasTokens() || (!isLoading && !profile)) {
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

      <div className={styles.menuAnchor}>
        <div
          className={styles.avatar}
          onClick={toggle}
          onKeyDown={(e) => e.key === "Enter" && toggle()}
          role="button"
          tabIndex={0}
          aria-expanded={isOpen}
          aria-haspopup="true"
        >
          <User2 size={30} />
        </div>

        {isOpen && (
          <div className={styles.dropdown} role="menu">
            <div className={styles.dropdownHeader}>
              <div className={styles.avatarLarge}>
                <User2 size={40} />
              </div>
              <div>
                <p className={styles.fullName}>{profile?.fullName ?? profile?.authUsername}</p>
                {profile?.email && <p className={styles.email}>{profile.email}</p>}
              </div>
            </div>

            <div className={styles.divider} />

            <Link to={routes.profile} className={styles.link} role="menuitem">
              <User size={18} />
              <span>Профиль</span>
            </Link>

            <Link to={routes.settings} className={styles.link} role="menuitem">
              <Settings size={18} />
              <span>Настройки</span>
            </Link>

            <div className={styles.divider} />

            <button
              type="button"
              className={styles.logoutButton}
              role="menuitem"
              onPointerDown={(e) => {
                e.preventDefault()
                e.stopPropagation()
              }}
              onClick={handleLogout}
            >
              <LogOut size={18} />
              <span>Выйти</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
