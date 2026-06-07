import { authRepository } from "data/repositories/Auth"
import type { UpdateProfileRequest } from "./types"

export const profileRepository = {
  updateProfile: (req: UpdateProfileRequest) =>
    authRepository.updateProfile({
      fullName: req.fullName,
      city: req.city,
      age: req.age,
      gender: req.gender,
    }),
}

export type { Profile, ProfileRole, ProfileGender, UpdateProfileRequest } from "./types"