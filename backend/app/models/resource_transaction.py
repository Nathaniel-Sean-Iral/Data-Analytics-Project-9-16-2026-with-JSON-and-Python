from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class ResourceTransaction(Base):
    """Append-only audit trail for every change to a resource's stock level."""

    __tablename__ = "resource_transactions"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    performed_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)

    resource = relationship("ResourceItem", backref="transactions")
