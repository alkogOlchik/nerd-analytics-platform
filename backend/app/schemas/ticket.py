from pydantic import BaseModel, ConfigDict


class TicketBase(BaseModel):
    title: str
    description: str | None = None


class TicketCreate(TicketBase):
    pass


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
