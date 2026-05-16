from backend.app.db.session import engine
from backend.app.models.base import Base
from backend.app.models import ticket, user  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
