from pydantic import BaseModel


class WordCountItem(BaseModel):
    word: str
    count: int


class CategoryCountItem(BaseModel):
    category: str
    count: int


class DateCountItem(BaseModel):
    date: str
    count: int


class DateFloatItem(BaseModel):
    date: str
    avg_rating: float


class DateAutoPctItem(BaseModel):
    date: str
    auto_pct: float


class DateSentimentItem(BaseModel):
    date: str
    positive: int
    negative: int


class ForecastItem(BaseModel):
    date: str
    predicted_count: float
    lower_bound: float
    upper_bound: float


class HeatmapCountItem(BaseModel):
    day_of_week: int
    hour: int
    count: int


class HeatmapTtfrItem(BaseModel):
    day_of_week: int
    hour: int
    avg_ttfr_min: float


class ProductRatingItem(BaseModel):
    product: str
    avg_rating: float


class LatestNegativeReviewItem(BaseModel):
    review_id: str
    ticket_id: str | None
    comment: str | None
    rating: int
    created_at: str


class WorkloadItem(BaseModel):
    employee_id: str
    username: str
    open: int
    closed: int


class LeaderboardItem(BaseModel):
    employee_id: str
    username: str
    closed_count: int
    avg_ttfr_min: float
    avg_ttr_min: float
    sla_pct: float


class PriorityAvgItem(BaseModel):
    priority: str
    avg_min: float


class SlaComplianceItem(BaseModel):
    priority: str
    ttfr_ok_pct: float
    ttr_ok_pct: float


class AdminSatisfactionItem(BaseModel):
    employee_id: str
    username: str
    avg_rating: float


class ClassificationAccuracyItem(BaseModel):
    category: str
    total: int
    changed: int
    accuracy_pct: float


class TopActiveUserItem(BaseModel):
    client_id: str
    ticket_count: int
    open_count: int


class DemographicsItem(BaseModel):
    gender: str | None = None
    group: str | None = None
    city: str | None = None
    count: int


class RetentionBlock(BaseModel):
    d7_pct: float
    d14_pct: float
    d30_pct: float


class SlowestCategoryItem(BaseModel):
    category: str
    avg_ttr_min: float


class TicketAnomalyItem(BaseModel):
    category: str
    product: str
    count_48h: int
    rolling_avg: float
    z_score: float


# ── Dashboard responses ────────────────────────────────────────────────────────

class Dashboard1Response(BaseModel):
    dynamics: list[DateCountItem]
    total_tickets: int
    total_tickets_delta_pct: float
    active_tickets: int
    active_by_priority: dict[str, int]
    avg_lifetime_hours: float
    reopens_dynamics: list[DateCountItem]
    reopen_rate_pct: float
    satisfaction_dynamics: list[DateFloatItem]
    rating_distribution: dict[str, int]
    worst_products: list[ProductRatingItem]


class Dashboard2Response(BaseModel):
    auto_resolved_dynamics: list[DateAutoPctItem]
    current_auto_resolved_pct: float
    auto_resolved_delta_pct: float
    top_escalated_categories: list[CategoryCountItem]
    avg_time_ai_min: float
    avg_time_human_min: float
    top_ai_resolved_categories: list[CategoryCountItem]
    avg_messages_before_escalation: float
    classification_accuracy: list[ClassificationAccuracyItem]


class Dashboard3Response(BaseModel):
    workload: list[WorkloadItem]
    leaderboard: list[LeaderboardItem]
    ttfr_by_priority: list[PriorityAvgItem]
    ttr_by_priority: list[PriorityAvgItem]
    sla_compliance: list[SlaComplianceItem]
    sla_violations_by_category: list[CategoryCountItem]
    heatmap: list[HeatmapTtfrItem]
    satisfaction_by_admin: list[AdminSatisfactionItem]


class Dashboard4Response(BaseModel):
    total_users: int
    new_users_period: int
    top_active_users: list[TopActiveUserItem]
    by_gender: list[DemographicsItem]
    by_age_group: list[DemographicsItem]
    by_city: list[DemographicsItem]
    retention: RetentionBlock


class Dashboard5Response(BaseModel):
    top_keywords_positive: list[WordCountItem]
    top_keywords_negative: list[WordCountItem]
    top_categories: list[CategoryCountItem]
    sentiment_dynamics: list[DateSentimentItem]
    positive_share_pct: float
    rating_distribution: dict[str, int]
    latest_negative: list[LatestNegativeReviewItem]


class Dashboard6TicketsResponse(BaseModel):
    top_keywords: list[WordCountItem]
    top_categories: list[CategoryCountItem]
    dynamics: list[DateCountItem]
    anomalies: list[TicketAnomalyItem]
    by_city: list[DemographicsItem]
    by_age_group: list[DemographicsItem]
    heatmap: list[HeatmapCountItem]
    slowest_categories: list[SlowestCategoryItem]


class Dashboard6ForecastResponse(BaseModel):
    forecast: list[ForecastItem]
