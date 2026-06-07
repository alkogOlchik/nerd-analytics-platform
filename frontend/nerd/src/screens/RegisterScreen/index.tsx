import { type FormEvent, useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { ChevronDown } from "lucide-react"
import { useRegister } from "domain/Auth/useRegister"
import { authRepository } from "data/repositories/Auth"
import { useMe } from "domain/Auth/useMe"
import { routes } from "shared/utils/routes"
import styles from "./styles.module.scss"

const ERROR_MAP: Record<string, string> = {
  "Username already taken": "Такой логин уже занят",
  "Email already registered": "Этот email уже зарегистрирован",
  "Username or email already exists": "Логин или email уже зарегистрирован",
}

const extractError = (err: unknown): string => {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === "string") return ERROR_MAP[detail] ?? detail
  if (Array.isArray(detail)) return detail.map((d: { msg: string }) => d.msg).join(", ")
  return "Ошибка сервера"
}

export const RegisterScreen = () => {
  const { data: user } = useMe()
  const { mutateAsync: register, isPending } = useRegister()
  const navigate = useNavigate()

  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [age, setAge] = useState("")
  const [gender, setGender] = useState<"" | "male" | "female">("")
  const [city, setCity] = useState("")
  const [showOptional, setShowOptional] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (user && authRepository.hasTokens()) return <Navigate to={routes.main} replace />

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await register({
        username,
        email,
        password,
        ...(fullName && { full_name: fullName }),
        ...(age && { age: Number(age) }),
        ...(gender && { gender }),
        ...(city && { city }),
      })
      navigate(routes.main, { replace: true })
    } catch (err) {
      setError(extractError(err))
    }
  }

  return (
    <div className={styles.page}>
      <div className={`${styles.blob} ${styles.blob1}`} />
      <div className={`${styles.blob} ${styles.blob2}`} />

      <div className={styles.card}>
        <div className={styles.logo}>
          <img src="/logo.png" alt="Nerd" />
        </div>

        <h1 className={styles.title}>Создать аккаунт</h1>
        <p className={styles.subtitle}>Зарегистрируйтесь, чтобы продолжить</p>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="username">
              Имя пользователя *
            </label>
            <input
              id="username"
              className={styles.input}
              type="text"
              placeholder="user01"
              autoComplete="username"
              minLength={3}
              maxLength={64}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="email">
              Email *
            </label>
            <input
              id="email"
              className={styles.input}
              type="email"
              placeholder="user@example.com"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="password">
              Пароль *
            </label>
            <input
              id="password"
              className={styles.input}
              type="password"
              placeholder="минимум 6 символов"
              autoComplete="new-password"
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="button"
            className={`${styles.optionalToggle} ${showOptional ? styles.open : ""}`}
            onClick={() => setShowOptional((v) => !v)}
          >
            <ChevronDown size={16} />
            Дополнительная информация
          </button>

          {showOptional && (
            <div className={styles.optionalFields}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="fullName">
                  Полное имя
                </label>
                <input
                  id="fullName"
                  className={styles.input}
                  type="text"
                  placeholder="Иван Иванов"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="age">
                  Возраст
                </label>
                <input
                  id="age"
                  className={styles.input}
                  type="number"
                  placeholder="25"
                  min={1}
                  max={120}
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="gender">
                  Пол
                </label>
                <select
                  id="gender"
                  className={styles.select}
                  value={gender}
                  onChange={(e) => setGender(e.target.value as "" | "male" | "female")}
                >
                  <option value="">Не указан</option>
                  <option value="male">Мужской</option>
                  <option value="female">Женский</option>
                </select>
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
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </div>
            </div>
          )}

          <button className={styles.button} type="submit" disabled={isPending}>
            {isPending ? "Регистрируем..." : "Создать аккаунт"}
          </button>
        </form>

        <p className={styles.footer}>
          Уже есть аккаунт?{" "}
          <Link to={routes.login}>Войти</Link>
        </p>
      </div>
    </div>
  )
}
