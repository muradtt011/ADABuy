from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)

    is_admin: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    listings: Mapped[list["Listing"]] = relationship(back_populates="seller", cascade="all, delete-orphan")

    def get_id(self) -> str:
        return str(self.id)

class Listing(db.Model):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    category: Mapped[str] = mapped_column(db.String(80), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(db.Numeric(10, 2), nullable=False)

    image_filename: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Soft-delete keeps audit trail and enables the UC-05/UC-09 alternate flow "Listing deleted".
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    seller_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    seller: Mapped["User"] = relationship(back_populates="listings")

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_listings_price_nonnegative"),
        Index("ix_listings_title", "title"),
    )