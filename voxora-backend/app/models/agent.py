"""
Voxora Backend — Agent Studio Model.

Stores tenant-customized AI agent configuration, including persona, tone,
system prompt, voice settings, business knowledge glossary, and data governance rules.
"""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AgentConfig(Base, UUIDMixin, TimestampMixin):
    """Configuration for a tenant's AI business intelligence copilot."""

    __tablename__ = "agent_configs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Persona & Identity
    name: Mapped[str] = mapped_column(String(100), default="Voxora Executive Copilot", nullable=False)
    avatar: Mapped[str] = mapped_column(String(50), default="🤖", nullable=False)
    role_title: Mapped[str] = mapped_column(String(100), default="Chief Analytics Officer", nullable=False)
    description: Mapped[str] = mapped_column(
        Text,
        default="Strategic C-suite intelligence advisor synthesizing metrics into decisive executive briefings.",
        nullable=False,
    )
    tone: Mapped[str] = mapped_column(
        String(50),
        default="executive",
        nullable=False,
    )  # "executive", "analytical", "strategic", "technical"
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)

    # Prompt Management
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    greeting_message: Mapped[str] = mapped_column(
        Text,
        default="Good day. I am your Voxora Executive Copilot. What business metrics, revenue figures, or market insights shall we explore today?",
        nullable=False,
    )
    fallback_message: Mapped[str] = mapped_column(
        Text,
        default="I am focused exclusively on business intelligence, market trends, and organizational data. Please refine your inquiry around operational or financial metrics.",
        nullable=False,
    )

    # Voice & Audio
    voice_id: Mapped[str] = mapped_column(String(100), default="en-US-Journey-F", nullable=False)
    voice_speed: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    voice_pitch: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Knowledge & Governance
    allowed_data_areas: Mapped[list] = mapped_column(
        JSONB,
        default=lambda: ["Revenue & Finance", "Product Performance", "Customer Intelligence", "Regional Operations"],
        server_default='["Revenue & Finance", "Product Performance", "Customer Intelligence", "Regional Operations"]',
        nullable=False,
    )
    data_access_rules: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {"mask_pii": True, "read_only": True, "auto_visualize": True, "allow_sql_generation": True},
        server_default='{"mask_pii": true, "read_only": true, "auto_visualize": true, "allow_sql_generation": true}',
        nullable=False,
    )
    knowledge_glossary: Mapped[list] = mapped_column(
        JSONB,
        default=lambda: [
            {
                "term": "Gross Margin",
                "definition": "Gross Profit divided by Total Revenue expressed as a percentage.",
            },
            {
                "term": "AOV",
                "definition": "Average Order Value: Total Revenue divided by Total Order Count.",
            },
            {
                "term": "Customer Segments",
                "definition": "Enterprise, Mid-Market, and SMB client classification tiers.",
            },
            {
                "term": "Fiscal Year",
                "definition": "Standard calendar year ending December 31st.",
            },
        ],
        server_default='[{"term": "Gross Margin", "definition": "Gross Profit divided by Total Revenue expressed as a percentage."}, {"term": "AOV", "definition": "Average Order Value: Total Revenue divided by Total Order Count."}, {"term": "Customer Segments", "definition": "Enterprise, Mid-Market, and SMB client classification tiers."}, {"term": "Fiscal Year", "definition": "Standard calendar year ending December 31st."}]',
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="agent_config")

    def __repr__(self) -> str:
        return f"<AgentConfig {self.name} tenant={self.tenant_id}>"
