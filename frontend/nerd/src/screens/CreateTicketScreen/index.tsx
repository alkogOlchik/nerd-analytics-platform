import { type FormEvent, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { CheckCircle, Mail } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import { useCreateTicket, useCreateGuestTicket } from "domain/Tickets"
import { authRepository } from "data/repositories/Auth"
import { routes } from "shared/utils/routes"
import type { TicketProduct, TicketPriority } from "data/repositories/Tickets"
import styles from "./CreateTicketScreen.module.scss"

const PRODUCTS: TicketProduct[] = [
  "веб-сервис",
  "платёжный сервис",
  "мобильное приложение",
  "API интеграция",
  "личный кабинет",
  "аналитический модуль",
]

const PRIORITIES: { value: TicketPriority; label: string }[] = [
  { value: "low", label: "Низкий" },
  { value: "medium", label: "Средний" },
  { value: "high", label: "Высокий" },
]

const defaultDeadline = () => {
  const d = new Date()
  d.setDate(d.getDate() + 7)
  return d.toISOString().slice(0, 10)
}

type GuestSuccess = { email: string }

export const CreateTicketScreen = () => {
  const navigate = useNavigate()
  const isAuthenticated = authRepository.hasTokens()

  const [product, setProduct] = useState<TicketProduct | "">("")
  const [description, setDescription] = useState("")
  const [priority, setPriority] = useState<TicketPriority>("medium")
  const [guestEmail, setGuestEmail] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [createdId, setCreatedId] = useState<string | null>(null)
  const [guestSuccess, setGuestSuccess] = useState<GuestSuccess | null>(null)

  const { mutateAsync: createTicket, isPending: isPendingAuth } = useCreateTicket()
  const { mutateAsync: createGuestTicket, isPending: isPendingGuest } = useCreateGuestTicket()
  const isPending = isPendingAuth || isPendingGuest

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!product) {
      setError("Выберите продукт")
      return
    }
    if (!isAuthenticated && !description.trim()) {
      setError("Опишите вашу проблему")
      return
    }
    setError(null)

    try {
      if (isAuthenticated) {
        const ticket = await createTicket({
          product,
          priority,
          deadline: new Date(defaultDeadline()).toISOString(),
          description,
        })
        setCreatedId(ticket.id)
      } else {
        await createGuestTicket({
          product,
          priority,
          message: description,
          guestEmail,
        })
        setGuestSuccess({ email: guestEmail })
      }
    } catch {
      setError("Не удалось создать обращение. Попробуйте ещё раз.")
    }
  }

  if (guestSuccess) {
    return (
      <div className={styles.page}>
        <Sidebar />
        <main className={styles.main}>
          <div className={styles.header}>
            <h1 className={styles.pageTitle}>Создать обращение</h1>
            <UserMenu />
          </div>
          <div className={styles.content}>
            <div className={styles.success}>
              <div className={styles.successIcon}>
                <CheckCircle size={36} />
              </div>
              <h2 className={styles.successTitle}>Обращение создано</h2>
              <p className={styles.successSubtitle}>
                Ссылка для отслеживания статуса отправлена на{" "}
                <strong className={styles.emailHighlight}>{guestSuccess.email}</strong>
              </p>
              <div className={styles.registerCard}>
                <div className={styles.registerCardIcon}>
                  <Mail size={20} />
                </div>
                <div>
                  <p className={styles.registerCardTitle}>Зарегистрируйтесь, чтобы удобнее отслеживать обращения</p>
                  <p className={styles.registerCardText}>
                    В личном кабинете видны все ваши обращения, история статусов и уведомления.
                  </p>
                </div>
              </div>
              <div className={styles.successActions}>
                <button
                  className={styles.newBtn}
                  onClick={() => {
                    setProduct("")
                    setDescription("")
                    setPriority("medium")
                    setGuestEmail("")
                    setGuestSuccess(null)
                  }}
                >
                  Создать ещё
                </button>
                <Link to={routes.register} className={styles.newBtn}>
                  Зарегистрироваться
                </Link>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (createdId) {
    return (
      <div className={styles.page}>
        <Sidebar />
        <main className={styles.main}>
          <div className={styles.header}>
            <h1 className={styles.pageTitle}>Создать обращение</h1>
            <UserMenu />
          </div>
          <div className={styles.content}>
            <div className={styles.success}>
              <div className={styles.successIcon}>
                <CheckCircle size={36} />
              </div>
              <h2 className={styles.successTitle}>Обращение создано</h2>
              <p className={styles.successSubtitle}>
                Мы рассмотрим ваше обращение в ближайшее время
              </p>
              <div className={styles.successActions}>
                <button
                  className={styles.newBtn}
                  onClick={() => {
                    setProduct("")
                    setDescription("")
                    setPriority("medium")
                    setCreatedId(null)
                  }}
                >
                  Создать ещё
                </button>
                <button
                  className={styles.newBtn}
                  onClick={() => navigate(routes.tickets)}
                >
                  Мои обращения
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Создать обращение</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="product">
                Продукт *
              </label>
              <select
                id="product"
                className={styles.select}
                value={product}
                onChange={(e) => setProduct(e.target.value as TicketProduct)}
                required
              >
                <option value="">Выберите продукт</option>
                {PRODUCTS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="description">
                Описание проблемы {!isAuthenticated && "*"}
              </label>
              <textarea
                id="description"
                className={styles.textarea}
                placeholder="Опишите вашу проблему подробнее..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required={!isAuthenticated}
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="priority">
                Приоритет
              </label>
              <select
                id="priority"
                className={styles.select}
                value={priority}
                onChange={(e) => setPriority(e.target.value as TicketPriority)}
              >
                {PRIORITIES.map(({ value, label }) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {!isAuthenticated && (
              <div className={styles.field}>
                <label className={styles.label} htmlFor="guestEmail">
                  Email для уведомления *
                </label>
                <input
                  id="guestEmail"
                  type="email"
                  className={styles.input}
                  placeholder="your@email.com"
                  value={guestEmail}
                  onChange={(e) => setGuestEmail(e.target.value)}
                  required
                />
                <span className={styles.fieldHint}>
                  Мы отправим ссылку для отслеживания статуса обращения
                </span>
              </div>
            )}

            {error && <div className={styles.error}>{error}</div>}

            <button className={styles.submit} type="submit" disabled={isPending}>
              {isPending ? "Создаём..." : "Создать обращение"}
            </button>

            {!isAuthenticated && (
              <p className={styles.loginHint}>
                Уже есть аккаунт?{" "}
                <Link to={routes.login} className={styles.loginLink}>
                  Войти
                </Link>
              </p>
            )}
          </form>
        </div>
      </main>
    </div>
  )
}
