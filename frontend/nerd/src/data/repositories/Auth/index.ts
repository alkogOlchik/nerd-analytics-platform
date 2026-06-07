import { authSource } from "data/sources/Auth"
import type { AuthTokens, LoginRequest, RegisterRequest, UserDto } from "data/sources/Auth"
import type { User } from "./types"

const getAccessToken = () => localStorage.getItem("access_token")
const getRefreshToken = () => localStorage.getItem("refresh_token")

const setTokens = (tokens: AuthTokens) => {
  localStorage.setItem("access_token", tokens.access_token)
  localStorage.setItem("refresh_token", tokens.refresh_token)
}

const clearTokens = () => {
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
}

const mapUserDto = (dto: UserDto): User => ({
  id: dto.id,
  username: dto.username,
  role: dto.role,
  email: dto.email,
  fullName: dto.full_name,
  age: dto.age,
  gender: dto.gender,
  city: dto.city,
  createdAt: dto.created_at,
})

// Если задана VITE_MOCK_USER_ROLE — позволяет работать без запущенного бэкенда.
// Допустимые значения: "employee" | "client"
// Пример: VITE_MOCK_USER_ROLE=employee в .env.local
const MOCK_ROLE = import.meta.env.VITE_MOCK_USER_ROLE as User["role"] | undefined

const MOCK_USER: User = {
  id: "mock-user-id",
  username: "mock_employee",
  role: MOCK_ROLE ?? "employee",
}

export const authRepository = {
  hasTokens: () => Boolean(getAccessToken()) || Boolean(MOCK_ROLE),
  getRefreshToken,
  clearTokens,
  setTokens,

  login: async (req: LoginRequest): Promise<User> => {
    const tokens = await authSource.login(req)
    setTokens(tokens)
    const dto = await authSource.me()
    return mapUserDto(dto)
  },

  register: async (req: RegisterRequest): Promise<User> => {
    await authSource.register(req)
    const tokens = await authSource.login({ username: req.username, password: req.password })
    setTokens(tokens)
    const dto = await authSource.me()
    return mapUserDto(dto)
  },

  logout: async (): Promise<void> => {
    const rt = getRefreshToken()
    clearTokens()
    if (rt) await authSource.logout(rt)
  },

  me: async (): Promise<User> => {
    if (MOCK_ROLE) return MOCK_USER
    const dto = await authSource.me()
    return mapUserDto(dto)
  },

  updateProfile: async (data: {
    fullName?: string
    city?: string
    age?: number
    gender?: string
  }): Promise<User> => {
    const dto = await authSource.updateProfile({
      full_name: data.fullName,
      city: data.city,
      age: data.age,
      gender: data.gender,
    })
    return mapUserDto(dto)
  },
}

export type { User, LoginRequest, RegisterRequest }