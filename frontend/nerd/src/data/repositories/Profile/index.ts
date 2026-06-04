import { profileSource } from "data/sources/Profile"
import type { LocalProfileData } from "data/sources/Profile"
import type { UpdateProfileRequest } from "./types"

export const profileRepository = {
  getLocalData: (): LocalProfileData | null => {
    return profileSource.getLocalData()
  },

  saveLocalData: (req: UpdateProfileRequest): void => {
    const data: LocalProfileData = {
      username: req.username,
      fullName: req.fullName,
      city: req.city,
      age: req.age,
      gender: req.gender,
    }
    profileSource.saveLocalData(data)
  },
}

export type { Profile, ProfileRole, ProfileGender, UpdateProfileRequest } from "./types"
