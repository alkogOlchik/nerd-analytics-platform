export type { LoginRequest, RegisterRequest } from "data/sources/Auth"

export interface User {
  id: string
  username: string
  role: "client" | "employee"
  email?: string
  fullName?: string
  age?: number
  gender?: string
  city?: string
  createdAt?: string
}
