import { useState, type MouseEvent } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"
import { clearAuthSession } from "domain/Auth/clearAuthSession"
import { useMe } from "domain/Auth/useMe"
import { routes } from "shared/utils/routes"
import { getDisplayName } from "modules/UserMenu/utils"

export const useUserMenu = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()

  const hasTokens = authRepository.hasTokens()
  const { data: user, isLoading } = useMe()

  const displayName = getDisplayName(user)

  const toggle = () => setIsOpen((v) => !v)

  const handleLogout = async (e: MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsOpen(false)
    await clearAuthSession(queryClient)
    window.location.assign(routes.login)
  }

  return {
    user: hasTokens ? user : undefined,
    isLoading: hasTokens && isLoading,
    isOpen,
    displayName,
    toggle,
    handleLogout,
  }
}
