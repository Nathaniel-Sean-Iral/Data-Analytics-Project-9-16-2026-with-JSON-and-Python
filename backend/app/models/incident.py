from sqlalchemy import Column, Float, Integer, String, Text

from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    barangay = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False, default="reported")
    description = Column(Text, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    affected_households = Column(Integer, nullable=True)
    reported_by = Column(String, nullable=True)
    reported_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
