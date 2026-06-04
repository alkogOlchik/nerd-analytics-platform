import { type FormEvent, useEffect, useRef, useState } from "react"
import { useUpdateProfile } from "domain/Profile"
import type { Profile } from "data/repositories/Profile"
import type { EditProfileFormErrors, EditProfileFormFields } from "../../types"
import { VALIDATION_MESSAGES } from "../../constants"

const validate = (fields: EditProfileFormFields): EditProfileFormErrors => {
  const errors: EditProfileFormErrors = {}
  if (fields.username && fields.username.trim().length < 3) {
    errors.username = VALIDATION_MESSAGES.usernameMinLength
  }
  if (fields.fullName && fields.fullName.trim().length < 2) {
    errors.fullName = VALIDATION_MESSAGES.fullNameMinLength
  }
  if (fields.age) {
    const n = parseInt(fields.age, 10)
    if (isNaN(n)) {
      errors.age = VALIDATION_MESSAGES.ageInvalid
    } else if (n < 1 || n > 120) {
      errors.age = VALIDATION_MESSAGES.ageRange
    }
  }
  return errors
}

export const useEditProfileForm = (profile: Profile | undefined) => {
  const [fields, setFields] = useState<EditProfileFormFields>({
    username: "",
    fullName: "",
    city: "",
    age: "",
    gender: "",
  })
  const [errors, setErrors] = useState<EditProfileFormErrors>({})

  const initialized = useRef(false)
  useEffect(() => {
    if (profile && !initialized.current) {
      initialized.current = true
      setFields({
        username: profile.username ?? profile.authUsername,
        fullName: profile.fullName ?? "",
        city: profile.city ?? "",
        age: profile.age?.toString() ?? "",
        gender: profile.gender ?? "",
      })
    }
  }, [profile])

  const { mutate: updateProfile, isPending, isSuccess, isError, reset } = useUpdateProfile()

  const setField = <K extends keyof EditProfileFormFields>(
    key: K,
    value: EditProfileFormFields[K],
  ) => {
    setFields((prev) => ({ ...prev, [key]: value }))
    if (errors[key as keyof EditProfileFormErrors]) {
      setErrors((prev) => ({ ...prev, [key]: undefined }))
    }
    if (isSuccess || isError) reset()
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const validationErrors = validate(fields)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }
    setErrors({})
    updateProfile({
      username: fields.username.trim() || undefined,
      fullName: fields.fullName.trim() || undefined,
      city: fields.city.trim() || undefined,
      age: fields.age ? parseInt(fields.age, 10) : undefined,
      gender: fields.gender || undefined,
    })
  }

  return { fields, setField, errors, isPending, isSuccess, isError, handleSubmit }
}
