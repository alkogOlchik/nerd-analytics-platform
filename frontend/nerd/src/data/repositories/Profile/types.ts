export type ProfileRole = "employee" | "client"
export type ProfileGender = "male" | "female" | "other"

export interface Profile {
  id: string
  authUsername: string
  email: string | undefined
  createdAt: string | undefined
  role: ProfileRole
  username: string | null
  fullName: string | null
  city: string | null
  age: number | null
  gender: ProfileGender | null
  hasLocalData: boolean
}

export interface UpdateProfileRequest {
  username?: string
  fullName?: string
  city?: string
  age?: number
  gender?: string
}
