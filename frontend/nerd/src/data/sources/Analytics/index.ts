import { apiClient } from "data/apiClient"
import type {
  AnalyticsParams,
  TicketSummaryDto,
  SlaDto,
  AiAccuracyDto,
  ReviewsSummaryDto,
  ReviewsKeywordsDto,
  TicketTimelineDto,
  AiEfficiencyDto,
  AdminWorkloadDto,
  AdminSlaDto,
  UserDemographicsDto,
  UserRetentionDto,
  ReviewDynamicsDto,
  TicketAnomaliesDto,
  TicketForecastDto,
  Dashboard6TicketsDto,
} from "./types"

const toApiParams = (params?: AnalyticsParams) => {
  if (!params) return undefined
  const { date_from, date_to, ...rest } = params
  return {
    ...rest,
    date_from: date_from ? `${date_from}T00:00:00Z` : undefined,
    date_to: date_to ? `${date_to}T23:59:59Z` : undefined,
  }
}

export const analyticsSource = {
  getTicketSummary: (params?: AnalyticsParams) =>
    apiClient.get<TicketSummaryDto>("/analytics/tickets/summary", { params: toApiParams(params) }).then((r) => r.data),

  getSla: (params?: AnalyticsParams) =>
    apiClient.get<SlaDto>("/analytics/tickets/sla", { params: toApiParams(params) }).then((r) => r.data),

  getAiAccuracy: (params?: AnalyticsParams) =>
    apiClient.get<AiAccuracyDto>("/analytics/ai/accuracy", { params: toApiParams(params) }).then((r) => r.data),

  getReviewsSummary: (params?: AnalyticsParams) =>
    apiClient.get<ReviewsSummaryDto>("/analytics/reviews/summary", { params: toApiParams(params) }).then((r) => r.data),

  getReviewsKeywords: (params?: AnalyticsParams) =>
    apiClient.get<ReviewsKeywordsDto>("/analytics/reviews/keywords", { params: toApiParams(params) }).then((r) => r.data),

  getTicketTimeline: (params?: AnalyticsParams) =>
    apiClient.get<TicketTimelineDto>("/analytics/tickets/timeline", { params: toApiParams(params) }).then((r) => r.data),

  getAiEfficiency: (params?: AnalyticsParams) =>
    apiClient.get<AiEfficiencyDto>("/analytics/ai/efficiency", { params: toApiParams(params) }).then((r) => r.data),

  getAdminWorkload: (params?: AnalyticsParams) =>
    apiClient.get<AdminWorkloadDto>("/analytics/admin/workload", { params: toApiParams(params) }).then((r) => r.data),

  getAdminSla: (params?: AnalyticsParams) =>
    apiClient.get<AdminSlaDto>("/analytics/admin/sla", { params: toApiParams(params) }).then((r) => r.data),

  getUserDemographics: (params?: AnalyticsParams) =>
    apiClient.get<UserDemographicsDto>("/analytics/users/demographics", { params: toApiParams(params) }).then((r) => r.data),

  getUserRetention: (params?: AnalyticsParams) =>
    apiClient.get<UserRetentionDto>("/analytics/users/retention", { params: toApiParams(params) }).then((r) => r.data),

  getReviewsDynamics: (params?: AnalyticsParams) =>
    apiClient.get<ReviewDynamicsDto>("/analytics/reviews/dynamics", { params: toApiParams(params) }).then((r) => r.data),

  getTicketAnomalies: (params?: AnalyticsParams) =>
    apiClient.get<TicketAnomaliesDto>("/analytics/tickets/anomalies", { params: toApiParams(params) }).then((r) => r.data),

  getTicketForecast: (params?: Pick<AnalyticsParams, "product" | "category">) =>
    apiClient.get<TicketForecastDto>("/analytics/tickets/forecast", { params }).then((r) => r.data),

  getDashboard6Tickets: (params?: AnalyticsParams) =>
    apiClient.get<Dashboard6TicketsDto>("/analytics/dashboard/6/tickets", { params: toApiParams(params) }).then((r) => r.data),
}

export type {
  AnalyticsParams,
  TicketSummaryDto,
  SlaDto,
  AiAccuracyDto,
  ReviewsSummaryDto,
  ReviewsKeywordsDto,
  KeyCountDto,
  TicketTimelineDto,
  AiEfficiencyDto,
  AdminWorkloadDto,
  AdminSlaDto,
  UserDemographicsDto,
  UserRetentionDto,
  ReviewDynamicsDto,
  TicketAnomaliesDto,
  TicketForecastDto,
  Dashboard6TicketsDto,
} from "./types"
