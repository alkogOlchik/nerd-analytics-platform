from pydantic import BaseModel


class DateCountItem(BaseModel):
    date: str
    count: int


class TicketDynamicsResponse(BaseModel):
    items: list[DateCountItem]


class TicketReopensResponse(BaseModel):
    total_closed: int
    total_reopened: int
    reopen_rate_pct: float


class CategoryCountItem(BaseModel):
    category: str
    count: int


class AIEfficiencyResponse(BaseModel):
    auto_resolved: int
    escalated: int
    auto_resolved_pct: float
    avg_messages_before_escalation: float
    top_escalated_categories: list[CategoryCountItem]
    top_resolved_categories: list[CategoryCountItem]


class AdminWorkloadItem(BaseModel):
    employee_id: str
    username: str
    open_tickets: int
    closed_tickets: int


class AdminWorkloadResponse(BaseModel):
    items: list[AdminWorkloadItem]


class SLAPriorityItem(BaseModel):
    priority: str
    avg_ttfr: float
    avg_ttr: float
    sla_ttfr_compliance_pct: float
    sla_ttr_compliance_pct: float


class AdminSLAResponse(BaseModel):
    by_priority: list[SLAPriorityItem]
    top_violated_categories: list[CategoryCountItem]


class HeatmapItem(BaseModel):
    day_of_week: int
    hour: int
    avg_ttfr_min: float


class HeatmapResponse(BaseModel):
    items: list[HeatmapItem]


class DemographicsCountItem(BaseModel):
    key: str
    count: int


class UserDemographicsResponse(BaseModel):
    by_gender: list[DemographicsCountItem]
    by_age_group: list[DemographicsCountItem]
    by_city: list[DemographicsCountItem]


class UserRetentionResponse(BaseModel):
    retention_7d_pct: float
    retention_14d_pct: float
    retention_30d_pct: float


class ReviewDynamicsItem(BaseModel):
    date: str
    positive_count: int
    negative_count: int


class ReviewDynamicsResponse(BaseModel):
    items: list[ReviewDynamicsItem]


class TicketAnomalyItem(BaseModel):
    category: str
    product: str
    count_48h: int
    rolling_avg: float
    stddev: float
    z_score: float


class TicketAnomaliesResponse(BaseModel):
    items: list[TicketAnomalyItem]
