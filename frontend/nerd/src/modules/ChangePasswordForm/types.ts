export interface ChangePasswordFormProps {
  className?: string
}

export interface ChangePasswordFormFields {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export interface ChangePasswordFormErrors {
  currentPassword?: string
  newPassword?: string
  confirmPassword?: string
}
