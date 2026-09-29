from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class EvacuationAssignment(Base):
    """One household placed in one evacuation center by a single allocation run.

    Rows are keyed by ``request_id`` so a whole run can be retrieved or rolled
    back. ``occupants`` is the household's own size, not a constant 1: a family of
    six consumes six center places.
    """

    __tablename__ = "evacuation_assignments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, nullable=False, index=True)
    household_id = Column(Integer, ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    center_id = Column(Integer, ForeignKey("evacuation_centers.id", ondelete="CASCADE"), nullable=False, index=True)
    occupants = Column(Integer, nullable=False, default=1)
    distance_km = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="assigned")
    assigned_at = Column(DateTime(timezone=True), nullable=False, index=True)

    household = relationship("Household", backref="assignments")
    center = relationship("EvacuationCenter", backref="assignments")
