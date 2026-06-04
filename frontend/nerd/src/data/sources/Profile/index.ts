import { PROFILE_STORAGE_KEY } from "./constants"
import type { LocalProfileData } from "./types"

export const profileSource = {
  getLocalData: (): LocalProfileData | null => {
    try {
      const raw = localStorage.getItem(PROFILE_STORAGE_KEY)
      return raw ? (JSON.parse(raw) as LocalProfileData) : null
    } catch {
      return null
    }
  },

  saveLocalData: (data: LocalProfileData): void => {
    const existing = profileSource.getLocalData() ?? {}
    const merged = { ...existing, ...data }
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(merged))
  },
}

export type { LocalProfileData }
