from sqlalchemy import Column, Float, Integer, String

from app.core.database import Base


class Household(Base):
    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    household_no = Column(String(40), unique=True, index=True, nullable=False)
    head_name = Column(String(120), nullable=False, index=True)
    address = Column(String(255), nullable=False)
    barangay = Column(String(80), nullable=False, index=True)
    size = Column(Integer, nullable=False, default=1)
    children_count = Column(Integer, nullable=False, default=0)
    elderly_count = Column(Integer, nullable=False, default=0)
    pwd_count = Column(Integer, nullable=False, default=0)
    contact = Column(String(40), nullable=True)
    lat = Column(Float, nullable=False, default=0.0)
    lng = Column(Float, nullable=False, default=0.0)
    notes = Column(String(500), nullable=True)