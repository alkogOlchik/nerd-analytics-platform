export interface KeyCount {
  key: string
  count: number
}

export interface TicketSummary {
  byStatus: KeyCount[]
  byProduct: KeyCount[]
  byCategory: KeyCount[]
}

export interface Sla {
  total: number
  breached: number
  compliant: number
  complianceRate: number
}

export interface AiAccuracy {
  totalClassified: number
  adminChanged: number
  accuracyRate: number
}

export interface ReviewsSummary {
  averageRating: number
  totalReviews: number
  sentimentDistribution: KeyCount[]
}

export interface ReviewsKeywords {
  keywordsPositive: KeyCount[]
  keywordsNegative: KeyCount[]
}

export interface AnalyticsFilters {
  from?: string
  to?: string
  product?: string
  category?: string
}
