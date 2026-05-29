import { type FormEvent, useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { useLogin } from "domain/Auth/useLogin"
import { useMe } from "domain/Auth/useMe"
import { routes } from "shared/utils/routes"
import styles from "./styles.module.scss"

const extractError = (err: unknown): string => {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) return detail.map((d: { msg: string }) => d.msg).join(", ")
  return "Ошибка сервера"
}

export const LoginScreen = () => {
  const { data: user } = useMe()
  const { mutateAsync: login, isPending } = useLogin()
  const navigate = useNavigate()

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)

  if (user) return <Navigate to={routes.main} replace />

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await login({ username, password })
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

        <h1 className={styles.title}>Добро пожаловать</h1>
        <p className={styles.subtitle}>Войдите в свой аккаунт</p>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="username">
              Имя пользователя
            </label>
            <input
              id="username"
              className={styles.input}
              type="text"
              placeholder="user01"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="password">
              Пароль
            </label>
            <input
              id="password"
              className={styles.input}
              type="password"
              placeholder="••••••"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button className={styles.button} type="submit" disabled={isPending}>
            {isPending ? "Входим..." : "Войти"}
          </button>
        </form>

        <p className={styles.footer}>
          Нет аккаунта?{" "}
          <Link to={routes.register}>Зарегистрироваться</Link>
        </p>
      </div>
    </div>
  )
}
