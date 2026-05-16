from sqlalchemy import Column, DateTime, Integer, String

from backend.app.models.base import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String)
    password_hash = Column(String)
    birth_date = Column(DateTime)
    telephone = Column(String)
    security_level = Column(String)
    position = Column(String)
