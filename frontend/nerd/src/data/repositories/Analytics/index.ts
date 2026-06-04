import { analyticsSource } from "data/sources/Analytics"
import type { KeyCountDto } from "data/sources/Analytics"
import type {
  KeyCount,
  TicketSummary,
  Sla,
  AiAccuracy,
  ReviewsSummary,
  ReviewsKeywords,
  AnalyticsFilters,
} from "./types"

const mapKeyCount = (dto: KeyCountDto): KeyCount => ({ key: dto.key, count: dto.count })

export const analyticsRepository = {
  getTicketSummary: async (filters?: AnalyticsFilters): Promise<TicketSummary> => {
    const dto = await analyticsSource.getTicketSummary(filters)
    return {
      byStatus: dto.by_status.map(mapKeyCount),
      byProduct: dto.by_product.map(mapKeyCount),
      byCategory: dto.by_category.map(mapKeyCount),
    }
  },

  getSla: async (filters?: AnalyticsFilters): Promise<Sla> => {
    const dto = await analyticsSource.getSla(filters)
    return {
      total: dto.total,
      breached: dto.breached,
      compliant: dto.compliant,
      complianceRate: dto.compliance_rate,
    }
  },

  getAiAccuracy: async (filters?: AnalyticsFilters): Promise<AiAccuracy> => {
    const dto = await analyticsSource.getAiAccuracy(filters)
    return {
      totalClassified: dto.total_classified,
      adminChanged: dto.admin_changed,
      accuracyRate: dto.accuracy_rate,
    }
  },

  getReviewsSummary: async (filters?: AnalyticsFilters): Promise<ReviewsSummary> => {
    const dto = await analyticsSource.getReviewsSummary(filters)
    return {
      averageRating: dto.average_rating,
      totalReviews: dto.total_reviews,
      sentimentDistribution: dto.sentiment_distribution.map(mapKeyCount),
    }
  },

  getReviewsKeywords: async (filters?: AnalyticsFilters): Promise<ReviewsKeywords> => {
    const dto = await analyticsSource.getReviewsKeywords(filters)
    return {
      keywordsPositive: dto.keywords_positive.map(mapKeyCount),
      keywordsNegative: dto.keywords_negative.map(mapKeyCount),
    }
  },
}

export type {
  KeyCount,
  TicketSummary,
  Sla,
  AiAccuracy,
  ReviewsSummary,
  ReviewsKeywords,
  AnalyticsFilters,
} from "./types"
