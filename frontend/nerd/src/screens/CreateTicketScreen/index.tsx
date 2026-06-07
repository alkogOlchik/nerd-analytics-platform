import { type FormEvent, useState } from "react"
import { useNavigate } from "react-router-dom"
import { CheckCircle } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import { useCreateTicket } from "domain/Tickets"
import { routes } from "shared/utils/routes"
import styles from "./CreateTicketScreen.module.scss"

const PRODUCTS = [
  "веб-сервис",
  "ии-ассистент",
  "аналитический модуль",
  "личный кабинет",
  "уведомления",
  "страница обращений",
  "страница отзывов",
  "работа оператора",
] as const

const PRIORITIES = [
  { value: "low", label: "Низкий" },
  { value: "medium", label: "Средний" },
  { value: "high", label: "Высокий" },
] as const

const defaultDeadline = () => {
  const d = new Date()
  d.setDate(d.getDate() + 7)
  return d.toISOString().slice(0, 10)
}

export const CreateTicketScreen = () => {
  const navigate = useNavigate()
  const [product, setProduct] = useState<string>("")
  const [description, setDescription] = useState("")
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium")
  const [error, setError] = useState<string | null>(null)
  const [createdId, setCreatedId] = useState<string | null>(null)

  const { mutateAsync: createTicket, isPending } = useCreateTicket()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!product) {
      setError("Выберите продукт")
      return
    }
    setError(null)
    try {
      const ticket = await createTicket({
        product: product as (typeof PRODUCTS)[number],
        priority,
        deadline: new Date(defaultDeadline()).toISOString(),
        description,
      })
      setCreatedId(ticket.id)
    } catch {
      setError("Не удалось создать обращение. Попробуйте ещё раз.")
    }
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
                onChange={(e) => setProduct(e.target.value)}
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
                Описание проблемы
              </label>
              <textarea
                id="description"
                className={styles.textarea}
                placeholder="Опишите вашу проблему подробнее..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
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
                onChange={(e) => setPriority(e.target.value as typeof priority)}
              >
                {PRIORITIES.map(({ value, label }) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {error && <div className={styles.error}>{error}</div>}

            <button className={styles.submit} type="submit" disabled={isPending}>
              {isPending ? "Создаём..." : "Создать обращение"}
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}
