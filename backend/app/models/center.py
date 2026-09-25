from sqlalchemy import Column, Float, Integer, String

from app.db.base import Base


class EvacuationCenter(Base):
    __tablename__ = "evacuation_centers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    barangay = Column(String, nullable=False, index=True)
    address = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    current_occupants = Column(Integer, default=0)
    facilities = Column(String, default="")
    contact = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    status = Column(String, default="active")
