import { apiClient } from "data/apiClient"
import type { AuthTokens, LoginRequest, RegisterRequest, UserDto } from "./types"

export const authSource = {
  login: (req: LoginRequest) =>
    apiClient.post<AuthTokens>("/auth/login", req).then((r) => r.data),

  register: (req: RegisterRequest) =>
    apiClient.post<UserDto>("/auth/register", req).then((r) => r.data),

  logout: (refreshToken: string) =>
    apiClient
      .post("/auth/logout", { refresh_token: refreshToken }, {
        // 204 No Content — нормальный ответ
        validateStatus: (status) => status === 204 || (status >= 200 && status < 300),
      })
      .then(() => undefined),

  refresh: (refreshToken: string) =>
    apiClient.post<AuthTokens>("/auth/refresh", { refresh_token: refreshToken }).then((r) => r.data),

  me: () => apiClient.get<UserDto>("/auth/me").then((r) => r.data),

  updateProfile: (data: { full_name?: string; city?: string; age?: number; gender?: string }) =>
    apiClient.patch<UserDto>("/auth/me", data).then((r) => r.data),
}

export type { AuthTokens, LoginRequest, RegisterRequest, UserDto }