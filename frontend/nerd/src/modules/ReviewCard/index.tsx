import { Tag, Ticket } from "lucide-react"
import styles from "./styles.module.scss"
import type { ReviewCardProps } from "./types"
import { useReviewCard } from "./useLogic"

const SENTIMENT_CLASS: Record<string, string> = {
  positive: styles.sentimentPositive,
  neutral: styles.sentimentNeutral,
  negative: styles.sentimentNegative,
}

const CARD_SENTIMENT_CLASS: Record<string, string> = {
  positive: styles.cardPositive,
  neutral: styles.cardNeutral,
  negative: styles.cardNegative,
}

const KEYWORD_CLASS: Record<string, string> = {
  positive: styles.keywordPositive,
  neutral: styles.keywordNeutral,
  negative: styles.keywordNegative,
}

export const ReviewCard = ({ review }: ReviewCardProps) => {
  const {
    formattedDate,
    sentimentLabel,
    productLabel,
    categoryLabel,
    allKeywords,
    hasKeywords,
    hasComment,
    hasTicket,
  } = useReviewCard(review)

  const sentimentAccent = review.sentiment
    ? CARD_SENTIMENT_CLASS[review.sentiment]
    : styles.cardNoSentiment

  return (
    <div className={`${styles.card} ${sentimentAccent}`}>
      <div className={styles.topRow}>
        <div className={styles.leftGroup}>
          <span className={styles.productBadge}>
            <Tag size={11} />
            {productLabel}
          </span>

          <div className={styles.stars}>
            {[1, 2, 3, 4, 5].map((n) => (
              <span
                key={n}
                className={`${styles.star} ${n <= review.rating ? styles.starFilled : ""}`}
              >
                ★
              </span>
            ))}
            <span className={styles.ratingText}>{review.rating}/5</span>
          </div>
        </div>

        <span className={styles.date}>{formattedDate}</span>
      </div>

      {(sentimentLabel || categoryLabel || hasTicket) && (
        <div className={styles.tagsRow}>
          {sentimentLabel && review.sentiment && (
            <span
              className={`${styles.sentimentBadge} ${SENTIMENT_CLASS[review.sentiment]}`}
            >
              {sentimentLabel}
            </span>
          )}

          {categoryLabel && (
            <span className={styles.categoryBadge}>{categoryLabel}</span>
          )}

          {hasTicket && (
            <span className={styles.ticketBadge}>
              <Ticket size={10} />
              К обращению
            </span>
          )}
        </div>
      )}

      {hasComment && (
        <p className={styles.comment}>{review.comment}</p>
      )}

      {hasKeywords && (
        <div className={styles.keywords}>
          {allKeywords.map((kw, i) => (
            <span
              key={`${kw.text}-${i}`}
              className={`${styles.keyword} ${KEYWORD_CLASS[kw.type]}`}
            >
              {kw.text}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
