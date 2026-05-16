from sqlalchemy import Column, ForeignKey, Integer, String, Text

from backend.app.models.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="open")
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
