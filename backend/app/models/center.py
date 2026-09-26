from sqlalchemy import Column, Float, Integer, String, JSON

from app.core.database import Base


class EvacuationCenter(Base):
    __tablename__ = "evacuation_centers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    barangay = Column(String(80), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    capacity = Column(Integer, nullable=False, default=0)
    current_occupants = Column(Integer, nullable=False, default=0)
    facilities = Column(JSON, nullable=False, default=list)
    contact = Column(String(40), nullable=True)
    lat = Column(Float, nullable=False, default=0.0)
    lng = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="standby", index=True)  # active | standby | closed