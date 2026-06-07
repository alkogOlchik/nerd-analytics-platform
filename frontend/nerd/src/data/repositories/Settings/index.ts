import { settingsSource } from "data/sources/Settings"
import type { ChangePasswordRequest } from "./types"

export const settingsRepository = {
  changePassword: async (req: ChangePasswordRequest): Promise<void> => {
    await settingsSource.changePassword({
      current_password: req.currentPassword,
      new_password: req.newPassword,
    })
  },
}

export type { ChangePasswordRequest } from "./types"
