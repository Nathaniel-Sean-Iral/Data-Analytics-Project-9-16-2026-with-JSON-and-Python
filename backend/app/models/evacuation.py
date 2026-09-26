from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class EvacuationAssignment(Base):
    """A single household → center assignment produced by an allocation run."""

    __tablename__ = "evacuation_assignments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(40), nullable=False, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False, index=True)
    center_id = Column(Integer, ForeignKey("evacuation_centers.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=False, server_default=func.now())