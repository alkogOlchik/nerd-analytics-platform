import { useQuery } from "@tanstack/react-query"
import { useMe } from "domain/Auth/useMe"
import { profileRepository } from "data/repositories/Profile"
import type { Profile } from "data/repositories/Profile"

export const PROFILE_LOCAL_QUERY_KEY = ["profile", "local"] as const

const hasAnyData = (d: ReturnType<typeof profileRepository.getLocalData>): boolean =>
  Boolean(d && (d.username || d.fullName || d.city || d.age || d.gender))

export const useProfile = () => {
  const { data: user, isLoading: authLoading } = useMe()

  const { data: localData } = useQuery({
    queryKey: PROFILE_LOCAL_QUERY_KEY,
    queryFn: profileRepository.getLocalData,
    staleTime: Infinity,
  })

  const profile: Profile | undefined = user
    ? {
        id: user.id,
        authUsername: user.username,
        email: user.email,
        createdAt: user.createdAt,
        role: user.role as Profile["role"],
        username: localData?.username ?? null,
        fullName: localData?.fullName ?? null,
        city: localData?.city ?? null,
        age: localData?.age ?? null,
        gender: (localData?.gender as Profile["gender"]) ?? null,
        hasLocalData: hasAnyData(localData ?? null),
      }
    : undefined

  return { data: profile, isLoading: authLoading }
}
