from pydantic import BaseModel


class CountItem(BaseModel):
    key: str
    count: int


class TicketSummaryResponse(BaseModel):
    by_status: list[CountItem]
    by_product: list[CountItem]
    by_category: list[CountItem]


class SLAStatsResponse(BaseModel):
    total: int
    breached: int
    compliant: int
    compliance_rate: float


class AIAccuracyResponse(BaseModel):
    total_classified: int
    admin_changed: int
    accuracy_rate: float


class ReviewSummaryResponse(BaseModel):
    average_rating: float
    total_reviews: int
    sentiment_distribution: list[CountItem]


class ReviewKeywordsResponse(BaseModel):
    keywords_positive: list[CountItem]
    keywords_negative: list[CountItem]
