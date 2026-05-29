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

export const authRepository = {
  hasTokens: () => Boolean(getAccessToken()),
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
    const dto = await authSource.me()
    return mapUserDto(dto)
  },
}

export type { User, LoginRequest, RegisterRequest }
