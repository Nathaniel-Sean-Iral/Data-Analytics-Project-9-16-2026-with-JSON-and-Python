from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    type = Column(String(40), nullable=False, index=True)  # rice | water | medicine | ...
    unit = Column(String(40), nullable=False, default="pc")
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    threshold = Column(Integer, nullable=False, default=0)
    expiry = Column(DateTime, nullable=True)
    stored_in = Column(String(150), nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    transactions = relationship("StockTransaction", back_populates="resource", cascade="all, delete-orphan")


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    resource = relationship("Resource", back_populates="transactions")


# Keep a reference so alembic/importers can discover models uniformly.
__all__ = ["Resource", "StockTransaction"]