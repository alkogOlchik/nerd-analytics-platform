import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useMe } from "domain/Auth/useMe"
import { useLogout } from "domain/Auth/useLogout"
import { routes } from "shared/utils/routes"
import { getDisplayName } from "modules/UserMenu/utils"

export const useUserMenu = () => {
  const [isOpen, setIsOpen] = useState(false)

  const { data: user, isLoading } = useMe()
  const { mutateAsync: logout, isPending: isLoggingOut } = useLogout()
  const navigate = useNavigate()

  const displayName = getDisplayName(user)

  const toggle = () => setIsOpen((v) => !v)

  const handleLogout = async () => {
    await logout()
    navigate(routes.login, { replace: true })
  }

  return {
    user,
    isLoading,
    isOpen,
    isLoggingOut,
    displayName,
    toggle,
    handleLogout,
  }
}
