import { Link, useLocation } from "react-router-dom"
import styles from "./styles.module.scss"
import type { SidebarProps } from "./types"
import { NAVIGATION_ITEMS } from "./constants"
import Logo from "public/Logo-label.png"
import { LiquidWrapper } from "shared/ui/LiquidWrapper"

export const Sidebar = ({ onSelect }: SidebarProps) => {
  const location = useLocation()

  return (
    <aside className={styles.sidebar}>
      <img className={styles.logo} src={Logo} alt="Nerd Analytics Logo" />

      <nav className={styles.navigation}>
        {NAVIGATION_ITEMS.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path

          return (
            <Link
              key={item.id}
              to={item.path}
              className={styles.navLink}
              onClick={() => onSelect?.(item.id)}
            >
              <LiquidWrapper isActive={isActive} className={styles.navItem}>
                <div className={styles.left}>
                  <Icon size={20} />
                  <span>{item.label}</span>
                </div>
                {!!item.notifications && (
                  <LiquidWrapper alwaysActive>
                    <div className={styles.badge}>{item.notifications}</div>
                  </LiquidWrapper>
                )}
              </LiquidWrapper>
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
