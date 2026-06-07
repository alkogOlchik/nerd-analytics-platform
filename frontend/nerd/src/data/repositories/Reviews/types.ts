export type ReviewSentiment = "positive" | "neutral" | "negative"

export interface Review {
  id: string
  ticketId: string | null
  clientId: string
  product: string | null
  rating: number
  comment: string | null
  createdAt: string
  aiSuggestedCategory: string | null
  finalCategory: string | null
  isAdminChanged: boolean
  sentiment: ReviewSentiment | null
  keywordsPositive: string[]
  keywordsNeutral: string[]
  keywordsNegative: string[]
  confidence: number | null
}

export interface CreateReviewInput {
  ticketId?: string | null
  product?: string
  rating: number
  comment?: string
}

export interface UpdateReviewInput {
  rating?: number
  comment?: string
  product?: string
  finalCategory?: string
  isAdminChanged?: boolean
}
