import { MOCK_CURRENT_PASSWORD } from "./constants"
import type { ChangePasswordDto } from "./types"

const delay = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

export const settingsSource = {
  // Эндпоинт смены пароля отсутствует в API — мок до появления POST /auth/change-password.
  changePassword: async (data: ChangePasswordDto): Promise<void> => {
    await delay(500)
    if (data.current_password !== MOCK_CURRENT_PASSWORD) {
      throw new Error("Неверный текущий пароль")
    }
  },
}

export type { ChangePasswordDto }
