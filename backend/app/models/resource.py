from sqlalchemy import Column, Integer, String

from app.db.base import Base


class ResourceItem(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False, index=True)
    unit = Column(String, nullable=False)
    quantity_on_hand = Column(Integer, default=0)
    threshold = Column(Integer, default=0)
    expiry = Column(String, nullable=True)
    stored_in = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
