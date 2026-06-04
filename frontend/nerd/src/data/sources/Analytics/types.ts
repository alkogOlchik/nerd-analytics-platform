export interface AnalyticsParams {
  from?: string
  to?: string
  product?: string
  category?: string
}

export interface KeyCountDto {
  key: string
  count: number
}

export interface TicketSummaryDto {
  by_status: KeyCountDto[]
  by_product: KeyCountDto[]
  by_category: KeyCountDto[]
}

export interface SlaDto {
  total: number
  breached: number
  compliant: number
  compliance_rate: number
}

export interface AiAccuracyDto {
  total_classified: number
  admin_changed: number
  accuracy_rate: number
}

export interface ReviewsSummaryDto {
  average_rating: number
  total_reviews: number
  sentiment_distribution: KeyCountDto[]
}

export interface ReviewsKeywordsDto {
  keywords_positive: KeyCountDto[]
  keywords_negative: KeyCountDto[]
}
