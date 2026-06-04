import { type FormEvent, useState } from "react"
import { useChangePassword } from "domain/Settings"
import type { ChangePasswordFormErrors, ChangePasswordFormFields } from "../../types"
import { VALIDATION_MESSAGES, ERROR_MESSAGES, DEFAULT_ERROR } from "../../constants"

const EMPTY_FIELDS: ChangePasswordFormFields = {
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
}

const validate = (fields: ChangePasswordFormFields): ChangePasswordFormErrors => {
  const errors: ChangePasswordFormErrors = {}
  if (!fields.currentPassword) {
    errors.currentPassword = VALIDATION_MESSAGES.currentPasswordRequired
  }
  if (!fields.newPassword) {
    errors.newPassword = VALIDATION_MESSAGES.newPasswordMinLength
  } else if (fields.newPassword.length < 6) {
    errors.newPassword = VALIDATION_MESSAGES.newPasswordMinLength
  } else if (fields.newPassword === fields.currentPassword) {
    errors.newPassword = VALIDATION_MESSAGES.sameAsOld
  }
  if (!fields.confirmPassword) {
    errors.confirmPassword = VALIDATION_MESSAGES.confirmPasswordRequired
  } else if (fields.newPassword !== fields.confirmPassword) {
    errors.confirmPassword = VALIDATION_MESSAGES.passwordsMismatch
  }
  return errors
}

const extractError = (err: unknown): string => {
  const msg = (err as Error)?.message
  return ERROR_MESSAGES[msg] ?? DEFAULT_ERROR
}

export const useChangePasswordForm = () => {
  const [fields, setFields] = useState<ChangePasswordFormFields>(EMPTY_FIELDS)
  const [errors, setErrors] = useState<ChangePasswordFormErrors>({})
  const [serverError, setServerError] = useState<string | null>(null)

  const { mutateAsync: changePassword, isPending, isSuccess, reset } = useChangePassword()

  const setField = <K extends keyof ChangePasswordFormFields>(
    key: K,
    value: ChangePasswordFormFields[K],
  ) => {
    setFields((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
    if (serverError) setServerError(null)
    if (isSuccess) reset()
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const validationErrors = validate(fields)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }
    setErrors({})
    setServerError(null)
    try {
      await changePassword({
        currentPassword: fields.currentPassword,
        newPassword: fields.newPassword,
      })
      setFields(EMPTY_FIELDS)
    } catch (err) {
      setServerError(extractError(err))
    }
  }

  return { fields, setField, errors, serverError, isPending, isSuccess, handleSubmit }
}
