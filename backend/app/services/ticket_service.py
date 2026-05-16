from sqlalchemy.orm import Session

from backend.app.models.ticket import Ticket


def list_tickets(db: Session) -> list[Ticket]:
    return db.query(Ticket).all()
