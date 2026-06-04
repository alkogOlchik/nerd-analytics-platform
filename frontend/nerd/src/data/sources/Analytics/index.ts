import { apiClient } from "data/apiClient"
import type {
  AnalyticsParams,
  TicketSummaryDto,
  SlaDto,
  AiAccuracyDto,
  ReviewsSummaryDto,
  ReviewsKeywordsDto,
} from "./types"

export const analyticsSource = {
  getTicketSummary: (params?: AnalyticsParams) =>
    apiClient.get<TicketSummaryDto>("/analytics/tickets/summary", { params }).then((r) => r.data),

  getSla: (params?: AnalyticsParams) =>
    apiClient.get<SlaDto>("/analytics/tickets/sla", { params }).then((r) => r.data),

  getAiAccuracy: (params?: AnalyticsParams) =>
    apiClient.get<AiAccuracyDto>("/analytics/ai/accuracy", { params }).then((r) => r.data),

  getReviewsSummary: (params?: AnalyticsParams) =>
    apiClient.get<ReviewsSummaryDto>("/analytics/reviews/summary", { params }).then((r) => r.data),

  getReviewsKeywords: (params?: AnalyticsParams) =>
    apiClient.get<ReviewsKeywordsDto>("/analytics/reviews/keywords", { params }).then((r) => r.data),
}

export type {
  AnalyticsParams,
  TicketSummaryDto,
  SlaDto,
  AiAccuracyDto,
  ReviewsSummaryDto,
  ReviewsKeywordsDto,
  KeyCountDto,
} from "./types"
