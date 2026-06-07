import { type FormEvent, useState } from "react"
import { CheckCircle } from "lucide-react"
import { Sidebar, UserMenu } from "modules"
import { useCreateReview } from "domain/Reviews/useCreateReview"
import styles from "./FeedbackScreen.module.scss"

const PRODUCTS = [
  "веб-сервис",
  "платёжный сервис",
  "мобильное приложение",
  "API интеграция",
  "личный кабинет",
  "аналитический модуль",
]

export const FeedbackScreen = () => {
  const [product, setProduct] = useState("")
  const [rating, setRating] = useState(0)
  const [hover, setHover] = useState(0)
  const [comment, setComment] = useState("")
  const [submitted, setSubmitted] = useState(false)

  const { mutateAsync: createReview, isPending } = useCreateReview()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!rating) return
    await createReview({ product: product || undefined, rating, comment: comment || undefined })
    setSubmitted(true)
  }

  const reset = () => {
    setProduct("")
    setRating(0)
    setHover(0)
    setComment("")
    setSubmitted(false)
  }

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Написать отзыв</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          {submitted ? (
            <div className={styles.success}>
              <div className={styles.successIcon}>
                <CheckCircle size={36} />
              </div>
              <h2 className={styles.successTitle}>Спасибо за отзыв!</h2>
              <p className={styles.successSubtitle}>Ваш отзыв поможет нам стать лучше</p>
              <button className={styles.newBtn} onClick={reset}>
                Написать ещё
              </button>
            </div>
          ) : (
            <form className={styles.form} onSubmit={handleSubmit}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="product">
                  Продукт
                </label>
                <select
                  id="product"
                  className={styles.select}
                  value={product}
                  onChange={(e) => setProduct(e.target.value)}
                >
                  <option value="">Не указан</option>
                  {PRODUCTS.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>

              <div className={styles.field}>
                <span className={styles.label}>Оценка *</span>
                <div className={styles.stars}>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      type="button"
                      className={`${styles.star} ${n <= (hover || rating) ? styles.starActive : ""}`}
                      onMouseEnter={() => setHover(n)}
                      onMouseLeave={() => setHover(0)}
                      onClick={() => setRating(n)}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="comment">
                  Комментарий
                </label>
                <textarea
                  id="comment"
                  className={styles.textarea}
                  placeholder="Расскажите подробнее..."
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                />
              </div>

              <button className={styles.submit} type="submit" disabled={isPending || !rating}>
                {isPending ? "Отправляем..." : "Отправить отзыв"}
              </button>
            </form>
          )}
        </div>
      </main>
    </div>
  )
}
