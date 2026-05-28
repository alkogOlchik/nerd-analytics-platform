import { apiClient } from "data/apiClient"
import type { AuthTokens, LoginRequest, RegisterRequest, UserDto } from "./types"

export const authSource = {
  login: (req: LoginRequest) =>
    apiClient.post<AuthTokens>("/auth/login", req).then((r) => r.data),

  register: (req: RegisterRequest) =>
    apiClient.post<UserDto>("/auth/register", req).then((r) => r.data),

  logout: (refreshToken: string) =>
    apiClient.post<void>("/auth/logout", { refresh_token: refreshToken }).then(() => undefined),

  refresh: (refreshToken: string) =>
    apiClient.post<AuthTokens>("/auth/refresh", { refresh_token: refreshToken }).then((r) => r.data),

  me: () => apiClient.get<UserDto>("/auth/me").then((r) => r.data),
}

export type { AuthTokens, LoginRequest, RegisterRequest, UserDto }
