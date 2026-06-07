import uuid
from typing import Any

from pydantic import BaseModel


class DateRange(BaseModel):
    from_: str | None = None
    to: str | None = None

    model_config = {"populate_by_name": True}


class DashboardContext(BaseModel):
    active_dashboard: int = 1
    current_filters: dict[str, Any] = {}
    date_range: DateRange = DateRange()


class AnalyticsChatRequest(BaseModel):
    session_id: uuid.UUID | None = None
    message: str
    dashboard_context: DashboardContext = DashboardContext()


class UiCommand(BaseModel):
    type: str
    field: str | None = None
    value: Any = None
    chart_id: str | None = None
    point_id: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class AnalyticsChatResponse(BaseModel):
    reply: str
    ui_commands: list[UiCommand] = []
    created_ticket_id: uuid.UUID | None = None
