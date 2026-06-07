import type { Review } from "data/repositories/Reviews"

const SENTIMENT_LABELS: Record<string, string> = {
  positive: "Позитивный",
  neutral: "Нейтральный",
  negative: "Негативный",
}

const PRODUCT_LABELS: Record<string, string> = {
  "веб-сервис": "Веб-сервис",
  "платёжный сервис": "Платёжный сервис",
  "мобильное приложение": "Мобильное приложение",
  "API интеграция": "API интеграция",
  "личный кабинет": "Личный кабинет",
  "аналитический модуль": "Аналитический модуль",
}

const formatDate = (iso: string) => {
  const date = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return `сегодня, ${date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}`
  }
  if (diffDays === 1) {
    return "вчера"
  }
  if (diffDays < 7) {
    return `${diffDays} дн. назад`
  }
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" })
}

export const useReviewCard = (review: Review) => {
  const formattedDate = formatDate(review.createdAt)
  const sentimentLabel = review.sentiment ? SENTIMENT_LABELS[review.sentiment] : null
  const productLabel = review.product ? (PRODUCT_LABELS[review.product] ?? review.product) : "Продукт не указан"
  const categoryLabel = review.finalCategory ?? review.aiSuggestedCategory

  const allKeywords = [
    ...review.keywordsPositive.map((k) => ({ text: k, type: "positive" as const })),
    ...review.keywordsNegative.map((k) => ({ text: k, type: "negative" as const })),
    ...review.keywordsNeutral.map((k) => ({ text: k, type: "neutral" as const })),
  ]

  return {
    formattedDate,
    sentimentLabel,
    productLabel,
    categoryLabel,
    allKeywords,
    hasKeywords: allKeywords.length > 0,
    hasComment: Boolean(review.comment),
    hasTicket: Boolean(review.ticketId),
  }
}
