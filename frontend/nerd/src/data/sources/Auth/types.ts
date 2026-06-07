export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
  age?: number
  gender?: "male" | "female"
  city?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserDto {
  id: string
  username: string
  role: "client" | "employee"
  email?: string
  full_name?: string
  age?: number
  gender?: string
  city?: string
  created_at?: string
}

export interface UpdateMeRequest {
  full_name?: string
  city?: string
  age?: number
  gender?: string
}
