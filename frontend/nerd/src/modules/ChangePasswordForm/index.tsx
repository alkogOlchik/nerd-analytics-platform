import { Lock, Eye, EyeOff, CheckCircle, AlertCircle } from "lucide-react"
import { useState } from "react"
import styles from "./styles.module.scss"
import type { ChangePasswordFormProps } from "./types"
import { useChangePasswordForm } from "./useLogic"

export const ChangePasswordForm = ({ className }: ChangePasswordFormProps) => {
  const { fields, setField, errors, serverError, isPending, isSuccess, handleSubmit } =
    useChangePasswordForm()

  const [show, setShow] = useState({ current: false, next: false, confirm: false })
  const toggleShow = (key: keyof typeof show) =>
    setShow((prev) => ({ ...prev, [key]: !prev[key] }))

  return (
    <div className={`${styles.card}${className ? ` ${className}` : ""}`}>
      <div className={styles.cardHeader}>
        <div className={styles.cardIcon}>
          <Lock size={18} />
        </div>
        <h2 className={styles.cardTitle}>Безопасность</h2>
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="currentPassword">
            Текущий пароль
          </label>
          <div className={styles.inputWrapper}>
            <input
              id="currentPassword"
              className={`${styles.input} ${errors.currentPassword ? styles.inputError : ""}`}
              type={show.current ? "text" : "password"}
              placeholder="••••••"
              autoComplete="current-password"
              value={fields.currentPassword}
              disabled={isPending}
              onChange={(e) => setField("currentPassword", e.target.value)}
            />
            <button
              type="button"
              className={styles.eyeButton}
              onClick={() => toggleShow("current")}
              tabIndex={-1}
            >
              {show.current ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.currentPassword && (
            <span className={styles.errorText}>{errors.currentPassword}</span>
          )}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="newPassword">
            Новый пароль
          </label>
          <div className={styles.inputWrapper}>
            <input
              id="newPassword"
              className={`${styles.input} ${errors.newPassword ? styles.inputError : ""}`}
              type={show.next ? "text" : "password"}
              placeholder="••••••"
              autoComplete="new-password"
              value={fields.newPassword}
              disabled={isPending}
              onChange={(e) => setField("newPassword", e.target.value)}
            />
            <button
              type="button"
              className={styles.eyeButton}
              onClick={() => toggleShow("next")}
              tabIndex={-1}
            >
              {show.next ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.newPassword && <span className={styles.errorText}>{errors.newPassword}</span>}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="confirmPassword">
            Подтвердить пароль
          </label>
          <div className={styles.inputWrapper}>
            <input
              id="confirmPassword"
              className={`${styles.input} ${errors.confirmPassword ? styles.inputError : ""}`}
              type={show.confirm ? "text" : "password"}
              placeholder="••••••"
              autoComplete="new-password"
              value={fields.confirmPassword}
              disabled={isPending}
              onChange={(e) => setField("confirmPassword", e.target.value)}
            />
            <button
              type="button"
              className={styles.eyeButton}
              onClick={() => toggleShow("confirm")}
              tabIndex={-1}
            >
              {show.confirm ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.confirmPassword && (
            <span className={styles.errorText}>{errors.confirmPassword}</span>
          )}
        </div>

        <div className={styles.footer}>
          {isSuccess && (
            <div className={`${styles.feedback} ${styles.feedbackSuccess}`}>
              <CheckCircle size={15} />
              <span>Пароль успешно изменён</span>
            </div>
          )}
          {serverError && (
            <div className={`${styles.feedback} ${styles.feedbackError}`}>
              <AlertCircle size={15} />
              <span>{serverError}</span>
            </div>
          )}
          <button className={styles.button} type="submit" disabled={isPending}>
            {isPending ? "Сохранение..." : "Сменить пароль"}
          </button>
        </div>
      </form>
    </div>
  )
}
