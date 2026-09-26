from sqlalchemy import Boolean, Column, Integer, String

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=True)
    role = Column(String(20), nullable=False, default="viewer", index=True)  # admin | responder | viewer
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)