import { useState, type MouseEvent } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"
import { clearAuthSession } from "domain/Auth/clearAuthSession"
import { useProfile } from "domain/Profile"
import { routes } from "shared/utils/routes"

export const useUserMenu = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()

  const hasTokens = authRepository.hasTokens()
  const { data: profile, isLoading } = useProfile()

  const displayName = profile?.fullName ?? profile?.authUsername ?? ""

  const toggle = () => setIsOpen((v) => !v)

  const handleLogout = async (e: MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsOpen(false)
    await clearAuthSession(queryClient)
    window.location.assign(routes.login)
  }

  return {
    profile: hasTokens ? profile : undefined,
    isLoading: hasTokens && isLoading,
    isOpen,
    displayName,
    toggle,
    handleLogout,
  }
}
