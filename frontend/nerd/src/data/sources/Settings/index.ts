import { apiClient } from "data/apiClient"
import type { ChangePasswordDto } from "./types"

export const settingsSource = {
  changePassword: async (data: ChangePasswordDto): Promise<void> => {
    await apiClient.post("/auth/change-password", data)
  },
}

export type { ChangePasswordDto }
