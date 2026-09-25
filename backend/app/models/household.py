from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from app.db.base import Base


class Household(Base):
    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    household_no = Column(String, unique=True, index=True, nullable=False)
    head_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    barangay = Column(String, nullable=False, index=True)
    size = Column(Integer, nullable=False, default=1)
    children_count = Column(Integer, default=0)
    elderly_count = Column(Integer, default=0)
    pwd_count = Column(Integer, default=0)
    contact = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
