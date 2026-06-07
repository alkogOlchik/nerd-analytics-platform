export const GENDER_OPTIONS = [
  { value: "male", label: "Мужской" },
  { value: "female", label: "Женский" },
] as const

export const VALIDATION_MESSAGES = {
  usernameMinLength: "Логин должен содержать минимум 3 символа",
  fullNameMinLength: "Имя должно содержать минимум 2 символа",
  ageRange: "Возраст должен быть от 1 до 120",
  ageInvalid: "Введите корректный возраст",
} as const
