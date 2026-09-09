"""
Voxora Backend — Role and Permission models.

RBAC: Roles grant permissions to access specific business areas.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Role(Base, UUIDMixin, TimestampMixin):
    """A role within a tenant that defines data access permissions."""

    __tablename__ = "roles"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions_matrix: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    users = relationship("User", back_populates="role", lazy="noload")
    permissions = relationship("Permission", back_populates="role", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class BusinessArea(Base, UUIDMixin, TimestampMixin):
    """A business area (e.g., Sales, Finance, HR) that can be permission-gated."""

    __tablename__ = "business_areas"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    allowed_datasets: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Relationships
    tenant = relationship("Tenant", back_populates="business_areas")
    permissions = relationship("Permission", back_populates="business_area", lazy="noload")

    def __repr__(self) -> str:
        return f"<BusinessArea {self.name}>"


class Permission(Base, UUIDMixin, TimestampMixin):
    """Links a role to a business area with a specific access level."""

    __tablename__ = "permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    business_area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_areas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="read"
    )  # "read", "write", "admin"

    # Relationships
    role = relationship("Role", back_populates="permissions")
    business_area = relationship("BusinessArea", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<Permission role={self.role_id} area={self.business_area_id} level={self.level}>"
