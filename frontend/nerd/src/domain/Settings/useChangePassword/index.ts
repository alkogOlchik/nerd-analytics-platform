import { useMutation } from "@tanstack/react-query"
import { settingsRepository } from "data/repositories/Settings"
import type { ChangePasswordRequest } from "data/repositories/Settings"

export const useChangePassword = () => {
  return useMutation({
    mutationFn: (req: ChangePasswordRequest) => settingsRepository.changePassword(req),
  })
}
