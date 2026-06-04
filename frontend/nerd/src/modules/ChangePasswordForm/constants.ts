export const VALIDATION_MESSAGES = {
  currentPasswordRequired: "Введите текущий пароль",
  newPasswordMinLength: "Минимум 6 символов",
  confirmPasswordRequired: "Подтвердите новый пароль",
  passwordsMismatch: "Пароли не совпадают",
  sameAsOld: "Новый пароль должен отличаться от текущего",
} as const

export const ERROR_MESSAGES: Record<string, string> = {
  "Неверный текущий пароль": "Неверный текущий пароль",
}

export const DEFAULT_ERROR = "Ошибка при смене пароля"
