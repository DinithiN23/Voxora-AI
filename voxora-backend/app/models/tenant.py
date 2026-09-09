"""
Voxora Backend — Tenant model.

Multi-tenant isolation: every resource belongs to exactly one tenant.
"""

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Tenant(Base, UUIDMixin, TimestampMixin):
    """A tenant represents a company/organization using Voxora."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Relationships
    users = relationship("User", back_populates="tenant", lazy="selectin")
    roles = relationship("Role", back_populates="tenant", lazy="selectin")
    business_areas = relationship("BusinessArea", back_populates="tenant", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"
