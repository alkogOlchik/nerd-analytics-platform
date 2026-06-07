import type { Profile } from "data/repositories/Profile"

export interface EditProfileFormProps {
  profile: Profile | undefined
  isProfileLoading?: boolean
}

export interface EditProfileFormFields {
  username: string
  fullName: string
  city: string
  age: string
  gender: string
}

export interface EditProfileFormErrors {
  username?: string
  fullName?: string
  age?: string
}
