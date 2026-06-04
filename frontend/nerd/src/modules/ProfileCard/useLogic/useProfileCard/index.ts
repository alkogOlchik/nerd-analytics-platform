import type { Profile } from "data/repositories/Profile"
import { ROLE_LABELS, GENDER_LABELS } from "../../constants"

const getInitials = (name: string): string => {
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}

const formatDate = (
  iso: string | undefined,
  opts: Intl.DateTimeFormatOptions,
): string | null => {
  if (!iso) return null
  const d = new Date(iso)
  if (isNaN(d.getTime())) return null
  return d.toLocaleDateString("ru-RU", { ...opts, timeZone: "UTC" })
}

const getAgeWord = (age: number): string => {
  const mod10 = age % 10
  const mod100 = age % 100
  if (mod100 >= 11 && mod100 <= 19) return "лет"
  if (mod10 === 1) return "год"
  if (mod10 >= 2 && mod10 <= 4) return "года"
  return "лет"
}

export const useProfileCard = (profile: Profile) => {
  const displayName = profile.fullName ?? profile.username ?? profile.authUsername
  const initials = getInitials(displayName)
  const roleLabel = ROLE_LABELS[profile.role] ?? profile.role
  const genderLabel = profile.gender ? (GENDER_LABELS[profile.gender] ?? profile.gender) : null
  const memberSince = formatDate(profile.createdAt, { month: "long", year: "numeric" })
  const registeredAt = formatDate(profile.createdAt, {
    day: "numeric",
    month: "long",
    year: "numeric",
  })
  const ageLabel = profile.age !== null ? `${profile.age} ${getAgeWord(profile.age)}` : null
  const displayUsername = profile.username ?? profile.authUsername

  return { initials, displayName, roleLabel, genderLabel, memberSince, registeredAt, ageLabel }
}
