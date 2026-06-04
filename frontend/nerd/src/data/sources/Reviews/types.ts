export type ReviewSentimentDto = "positive" | "neutral" | "negative"

export interface ReviewDto {
  id: string
  ticket_id: string | null
  client_id: string
  product: string | null
  rating: number
  comment: string | null
  created_at: string
  ai_suggested_category: string | null
  final_category: string | null
  is_admin_changed: boolean
  sentiment: ReviewSentimentDto | null
  keywords_positive: string[]
  keywords_neutral: string[]
  keywords_negative: string[]
  confidence: number | null
}

export interface CreateReviewRequest {
  ticket_id?: string | null
  product?: string
  rating: number
  comment?: string
}

export interface UpdateReviewRequest {
  rating?: number
  comment?: string
  product?: string
  final_category?: string
  is_admin_changed?: boolean
}

export interface ClassifyReviewRequest {
  review_id: string
  text: string
  model?: string
}
