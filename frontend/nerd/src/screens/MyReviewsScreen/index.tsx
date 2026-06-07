import { useState } from "react"
import { MessageSquareOff } from "lucide-react"
import styles from "./styles.module.scss"
import { Sidebar, UserMenu, ReviewCard } from "modules"
import { useReviews } from "domain/Reviews"
import type { ReviewSentiment } from "data/repositories/Reviews"

type SentimentFilter = "all" | ReviewSentiment
type RatingFilter = 0 | 1 | 2 | 3 | 4 | 5

const SENTIMENT_FILTERS: { value: SentimentFilter; label: string }[] = [
  { value: "all", label: "Все" },
  { value: "positive", label: "Позитивные" },
  { value: "neutral", label: "Нейтральные" },
  { value: "negative", label: "Негативные" },
]

export const MyReviewsScreen = () => {
  const [sentimentFilter, setSentimentFilter] = useState<SentimentFilter>("all")
  const [ratingFilter, setRatingFilter] = useState<RatingFilter>(0)

  const { data: reviews = [], isLoading } = useReviews()

  const filtered = reviews.filter((r) => {
    const sentimentOk =
      sentimentFilter === "all" || r.sentiment === sentimentFilter
    const ratingOk = ratingFilter === 0 || r.rating === ratingFilter
    return sentimentOk && ratingOk
  })

  const countBySentiment = (s: SentimentFilter) => {
    if (s === "all") return reviews.length
    return reviews.filter((r) => r.sentiment === s).length
  }

  const avgRating =
    reviews.length > 0
      ? (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)
      : "—"

  const positiveCount = reviews.filter((r) => r.sentiment === "positive").length
  const negativeCount = reviews.filter((r) => r.sentiment === "negative").length

  return (
    <div className={styles.page}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.pageTitle}>Мои отзывы</h1>
          <UserMenu />
        </div>

        <div className={styles.content}>
          {!isLoading && reviews.length > 0 && (
            <div className={styles.statsBar}>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{reviews.length}</span>
                <span className={styles.statLabel}>Всего отзывов</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{avgRating}</span>
                <span className={styles.statLabel}>Средняя оценка</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{positiveCount}</span>
                <span className={styles.statLabel}>Позитивных</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{negativeCount}</span>
                <span className={styles.statLabel}>Негативных</span>
              </div>
            </div>
          )}

          <div className={styles.toolbar}>
            <div className={styles.tabs}>
              {SENTIMENT_FILTERS.map(({ value, label }) => (
                <button
                  key={value}
                  className={`${styles.tab} ${sentimentFilter === value ? styles.tabActive : ""}`}
                  onClick={() => setSentimentFilter(value)}
                >
                  <span>{label}</span>
                  {!isLoading && (
                    <span className={styles.tabCount}>{countBySentiment(value)}</span>
                  )}
                </button>
              ))}
            </div>

            <div className={styles.ratingFilter}>
              <button
                className={`${styles.ratingBtn} ${ratingFilter === 0 ? styles.ratingBtnActive : ""}`}
                onClick={() => setRatingFilter(0)}
              >
                Все оценки
              </button>
              {([1, 2, 3, 4, 5] as const).map((n) => (
                <button
                  key={n}
                  className={`${styles.ratingBtn} ${ratingFilter === n ? styles.ratingBtnActive : ""}`}
                  onClick={() => setRatingFilter(n)}
                >
                  {"★".repeat(n)}
                </button>
              ))}
            </div>
          </div>

          {isLoading && (
            <div className={styles.loading}>
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
              <span className={styles.loadingDot} />
            </div>
          )}

          {!isLoading && filtered.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>
                <MessageSquareOff size={36} />
              </div>
              <h2 className={styles.emptyTitle}>
                {reviews.length === 0 ? "Отзывов ещё нет" : "Нет отзывов по фильтру"}
              </h2>
              <p className={styles.emptySubtitle}>
                {reviews.length === 0
                  ? "Вы ещё не оставляли отзывов. Поделитесь впечатлением о сервисе!"
                  : "Попробуйте изменить фильтры"}
              </p>
            </div>
          )}

          {!isLoading && filtered.length > 0 && (
            <div className={styles.list}>
              {filtered.map((review) => (
                <ReviewCard key={review.id} review={review} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
