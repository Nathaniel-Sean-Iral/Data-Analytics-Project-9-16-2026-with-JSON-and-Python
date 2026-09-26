from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    type = Column(String(40), nullable=False, index=True)  # flood | fire | earthquake | landslide | typhoon | other
    barangay = Column(String(80), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="moderate", index=True)  # low | moderate | high | critical
    status = Column(String(20), nullable=False, default="reported", index=True)  # reported | assessing | responding | resolved
    description = Column(String(2000), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    affected_households = Column(Integer, nullable=True, default=0)
    reported_by = Column(String(120), nullable=True)
    reported_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())