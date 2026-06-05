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
  TicketTimeline,
  AiEfficiency,
  AdminWorkload,
  AdminSla,
  UserDemographics,
  UserRetention,
  ReviewDynamics,
  TicketAnomalies,
  TicketForecast,
  Dashboard6Tickets,
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

  getTicketTimeline: async (filters?: AnalyticsFilters): Promise<TicketTimeline> => {
    const dto = await analyticsSource.getTicketTimeline(filters)
    return { items: dto.items }
  },

  getAiEfficiency: async (filters?: AnalyticsFilters): Promise<AiEfficiency> => {
    const dto = await analyticsSource.getAiEfficiency(filters)
    return {
      autoResolved: dto.auto_resolved,
      escalated: dto.escalated,
      autoResolvedPct: dto.auto_resolved_pct,
      avgMessagesBeforeEscalation: dto.avg_messages_before_escalation,
      topEscalatedCategories: dto.top_escalated_categories.map((c) => ({ category: c.category, count: c.count })),
      topResolvedCategories: dto.top_resolved_categories.map((c) => ({ category: c.category, count: c.count })),
    }
  },

  getAdminWorkload: async (filters?: AnalyticsFilters): Promise<AdminWorkload> => {
    const dto = await analyticsSource.getAdminWorkload(filters)
    return {
      items: dto.items.map((i) => ({
        employeeId: i.employee_id,
        username: i.username,
        openTickets: i.open_tickets,
        closedTickets: i.closed_tickets,
      })),
    }
  },

  getAdminSla: async (filters?: AnalyticsFilters): Promise<AdminSla> => {
    const dto = await analyticsSource.getAdminSla(filters)
    return {
      byPriority: dto.by_priority.map((p) => ({
        priority: p.priority,
        avgTtfr: p.avg_ttfr,
        avgTtr: p.avg_ttr,
        slaTtfrCompliancePct: p.sla_ttfr_compliance_pct,
        slaTtrCompliancePct: p.sla_ttr_compliance_pct,
      })),
      topViolatedCategories: dto.top_violated_categories.map((c) => ({ category: c.category, count: c.count })),
    }
  },

  getUserDemographics: async (filters?: AnalyticsFilters): Promise<UserDemographics> => {
    const dto = await analyticsSource.getUserDemographics(filters)
    return {
      byGender: dto.by_gender.map((g) => ({ key: g.key, count: g.count })),
      byAgeGroup: dto.by_age_group.map((a) => ({ key: a.key, count: a.count })),
      byCity: dto.by_city.map((c) => ({ key: c.key, count: c.count })),
    }
  },

  getUserRetention: async (filters?: AnalyticsFilters): Promise<UserRetention> => {
    const dto = await analyticsSource.getUserRetention(filters)
    return {
      retention7dPct: dto.retention_7d_pct,
      retention14dPct: dto.retention_14d_pct,
      retention30dPct: dto.retention_30d_pct,
    }
  },

  getReviewsDynamics: async (filters?: AnalyticsFilters): Promise<ReviewDynamics> => {
    const dto = await analyticsSource.getReviewsDynamics(filters)
    return {
      items: dto.items.map((i) => ({
        date: i.date,
        positiveCount: i.positive_count,
        negativeCount: i.negative_count,
      })),
    }
  },

  getTicketAnomalies: async (filters?: AnalyticsFilters): Promise<TicketAnomalies> => {
    const dto = await analyticsSource.getTicketAnomalies(filters)
    return {
      items: dto.items.map((i) => ({
        category: i.category,
        product: i.product,
        count48h: i.count_48h,
        rollingAvg: i.rolling_avg,
        stddev: i.stddev,
        zScore: i.z_score,
      })),
    }
  },

  getTicketForecast: async (params?: { product?: string; category?: string }): Promise<TicketForecast> => {
    const dto = await analyticsSource.getTicketForecast(params)
    return {
      forecast: dto.forecast.map((f) => ({
        date: f.date,
        predictedCount: f.predicted_count,
        lowerBound: f.lower_bound,
        upperBound: f.upper_bound,
      })),
    }
  },

  getDashboard6Tickets: async (filters?: AnalyticsFilters): Promise<Dashboard6Tickets> => {
    const dto = await analyticsSource.getDashboard6Tickets(filters)
    return {
      topKeywords: dto.top_keywords.map((w) => ({ word: w.word, count: w.count })),
      topCategories: dto.top_categories.map((c) => ({ category: c.category, count: c.count })),
      dynamics: dto.dynamics,
      anomalies: dto.anomalies.map((a) => ({
        category: a.category,
        product: a.product,
        count48h: a.count_48h,
        rollingAvg: a.rolling_avg,
        zScore: a.z_score,
      })),
      slowestCategories: dto.slowest_categories.map((s) => ({
        category: s.category,
        avgTtrMin: s.avg_ttr_min,
      })),
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
  TicketTimeline,
  TimelineItem,
  AiEfficiency,
  CategoryCount,
  AdminWorkload,
  AdminWorkloadItem,
  AdminSla,
  SlaPriorityItem,
  UserDemographics,
  DemographicsCountItem,
  UserRetention,
  ReviewDynamics,
  ReviewDynamicsItem,
  TicketAnomalies,
  TicketAnomalyItem,
  TicketForecast,
  ForecastItem,
  Dashboard6Tickets,
  WordCount,
  SlowestCategory,
  DashboardAnomalyItem,
} from "./types"
