import styles from "./styles.module.scss"
import type { SidebarProps } from "./types"
import { useSidebar } from "./useLogic"
import { NAVIGATION_ITEMS } from "./constants"
import Logo from "public/Logo-label.png"
import { LiquidWrapper } from "shared/ui/LiquidWrapper"

export const Sidebar = ({ onSelect }: SidebarProps) => {
  const { activeItem, handleSelect } = useSidebar()

  const onItemClick = (id: string) => {
    handleSelect(id)
    onSelect(id)
  }

  return (
    <aside className={styles.sidebar}>
      <img className={styles.logo} src={Logo} alt="Nerd Analytics Logo" />

      <nav className={styles.navigation}>
        {NAVIGATION_ITEMS.map((item) => {
          const Icon = item.icon

          return (
            <LiquidWrapper
              key={item.id}
              isActive={activeItem === item.id}
              onClick={() => onItemClick(item.id)}
              className={styles.navItem}
            >
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
          )
        })}
      </nav>
    </aside>
  )
}
