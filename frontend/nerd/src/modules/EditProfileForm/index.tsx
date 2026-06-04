import { User, CheckCircle, AlertCircle } from "lucide-react"
import styles from "./styles.module.scss"
import type { EditProfileFormProps } from "./types"
import { useEditProfileForm } from "./useLogic"
import { GENDER_OPTIONS } from "./constants"

export const EditProfileForm = ({ profile, isProfileLoading }: EditProfileFormProps) => {
  const { fields, setField, errors, isPending, isSuccess, isError, handleSubmit } =
    useEditProfileForm(profile)

  const disabled = isProfileLoading || isPending

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.cardIcon}>
          <User size={18} />
        </div>
        <h2 className={styles.cardTitle}>Личные данные</h2>
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.fieldFull}>
          <label className={styles.label} htmlFor="username">
            Логин
          </label>
          <input
            id="username"
            className={`${styles.input} ${errors.username ? styles.inputError : ""}`}
            type="text"
            placeholder="ivan.ivanov"
            value={fields.username}
            disabled={disabled}
            onChange={(e) => setField("username", e.target.value)}
          />
          {errors.username && <span className={styles.errorText}>{errors.username}</span>}
        </div>

        <div className={styles.fieldsGrid}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="fullName">
              Полное имя
            </label>
            <input
              id="fullName"
              className={`${styles.input} ${errors.fullName ? styles.inputError : ""}`}
              type="text"
              placeholder="Иван Иванов"
              value={fields.fullName}
              disabled={disabled}
              onChange={(e) => setField("fullName", e.target.value)}
            />
            {errors.fullName && <span className={styles.errorText}>{errors.fullName}</span>}
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="city">
              Город
            </label>
            <input
              id="city"
              className={styles.input}
              type="text"
              placeholder="Москва"
              value={fields.city}
              disabled={disabled}
              onChange={(e) => setField("city", e.target.value)}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="age">
              Возраст
            </label>
            <input
              id="age"
              className={`${styles.input} ${errors.age ? styles.inputError : ""}`}
              type="number"
              placeholder="25"
              min={1}
              max={120}
              value={fields.age}
              disabled={disabled}
              onChange={(e) => setField("age", e.target.value)}
            />
            {errors.age && <span className={styles.errorText}>{errors.age}</span>}
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="gender">
              Пол
            </label>
            <select
              id="gender"
              className={styles.input}
              value={fields.gender}
              disabled={disabled}
              onChange={(e) => setField("gender", e.target.value)}
            >
              {GENDER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className={styles.footer}>
          {isSuccess && (
            <div className={`${styles.feedback} ${styles.feedbackSuccess}`}>
              <CheckCircle size={15} />
              <span>Изменения сохранены</span>
            </div>
          )}
          {isError && (
            <div className={`${styles.feedback} ${styles.feedbackError}`}>
              <AlertCircle size={15} />
              <span>Ошибка при сохранении</span>
            </div>
          )}
          <button className={styles.button} type="submit" disabled={disabled}>
            {isPending ? "Сохранение..." : "Сохранить изменения"}
          </button>
        </div>
      </form>
    </div>
  )
}
