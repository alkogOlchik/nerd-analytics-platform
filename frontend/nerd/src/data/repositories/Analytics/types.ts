export interface KeyCount {
  key: string
  count: number
}

export interface AnalyticsFilters {
  date_from?: string
  date_to?: string
  product?: string
  priority?: string
  category?: string
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

// Timeline
export interface TimelineItem {
  date: string
  count: number
}

export interface TicketTimeline {
  items: TimelineItem[]
}

// AI Efficiency
export interface CategoryCount {
  category: string
  count: number
}

export interface AiEfficiency {
  autoResolved: number
  escalated: number
  autoResolvedPct: number
  avgMessagesBeforeEscalation: number
  topEscalatedCategories: CategoryCount[]
  topResolvedCategories: CategoryCount[]
}

// Admin Workload
export interface AdminWorkloadItem {
  employeeId: string
  username: string
  openTickets: number
  closedTickets: number
}

export interface AdminWorkload {
  items: AdminWorkloadItem[]
}

// Admin SLA
export interface SlaPriorityItem {
  priority: string
  avgTtfr: number
  avgTtr: number
  slaTtfrCompliancePct: number
  slaTtrCompliancePct: number
}

export interface AdminSla {
  byPriority: SlaPriorityItem[]
  topViolatedCategories: CategoryCount[]
}

// Users Demographics
export interface DemographicsCountItem {
  key: string
  count: number
}

export interface UserDemographics {
  byGender: DemographicsCountItem[]
  byAgeGroup: DemographicsCountItem[]
  byCity: DemographicsCountItem[]
}

// Users Retention
export interface UserRetention {
  retention7dPct: number
  retention14dPct: number
  retention30dPct: number
}

// Reviews Dynamics
export interface ReviewDynamicsItem {
  date: string
  positiveCount: number
  negativeCount: number
}

export interface ReviewDynamics {
  items: ReviewDynamicsItem[]
}

// Ticket Anomalies
export interface TicketAnomalyItem {
  category: string
  product: string
  count48h: number
  rollingAvg: number
  stddev: number
  zScore: number
}

export interface TicketAnomalies {
  items: TicketAnomalyItem[]
}

// Ticket Forecast
export interface ForecastItem {
  date: string
  predictedCount: number
  lowerBound: number
  upperBound: number
}

export interface TicketForecast {
  forecast: ForecastItem[]
}

// Dashboard 6 Tickets
export interface WordCount {
  word: string
  count: number
}

export interface SlowestCategory {
  category: string
  avgTtrMin: number
}

export interface DashboardAnomalyItem {
  category: string
  product: string
  count48h: number
  rollingAvg: number
  zScore: number
}

export interface Dashboard6Tickets {
  topKeywords: WordCount[]
  topCategories: CategoryCount[]
  dynamics: TimelineItem[]
  anomalies: DashboardAnomalyItem[]
  slowestCategories: SlowestCategory[]
}
