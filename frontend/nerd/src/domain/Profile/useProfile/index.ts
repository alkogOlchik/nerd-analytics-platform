import { useMe } from "domain/Auth/useMe"
import type { Profile } from "data/repositories/Profile"

export const PROFILE_LOCAL_QUERY_KEY = ["profile", "local"] as const

export const useProfile = () => {
  const { data: user, isLoading: authLoading } = useMe()

  const profile: Profile | undefined = user
    ? {
        id: user.id,
        authUsername: user.username,
        email: user.email,
        createdAt: user.createdAt,
        role: user.role as Profile["role"],
        username: user.username ?? null,
        fullName: user.fullName ?? null,
        city: user.city ?? null,
        age: user.age ?? null,
        gender: (user.gender as Profile["gender"]) ?? null,
        hasLocalData: Boolean(user.fullName || user.city || user.age || user.gender),
      }
    : undefined

  return { data: profile, isLoading: authLoading }
}
