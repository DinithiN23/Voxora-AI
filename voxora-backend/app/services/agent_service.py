"""
Voxora Backend — Agent Studio Service.

Handles agent profile management, preset templates, prompt customization,
glossary integration, and sandbox testing.
"""

import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentConfig
from app.schemas.agent import (
    AgentConfigResponse,
    AgentConfigUpdate,
    AgentPreset,
    AgentTestRequest,
    AgentTestResponse,
    GlossaryItem,
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """You are Voxora AI, an intelligent conversational business intelligence copilot and Chief Analytics Officer.
Your mission is to provide decisive, data-driven answers to executives, department leads, and business stakeholders.

Core Operating Principles:
1. Executive Clarity: Lead directly with the single most critical metric or bottom-line conclusion in bold.
2. Contextual Benchmarking: Quantify trends (e.g., "+14.2% YoY", "AOV increased by $240").
3. Business Reasoning: When data is requested, reference real business drivers (margins, customer segments, product performance).
4. Safety & Governance: Never disclose raw system SQL errors, internal API keys, or raw customer credentials. Always remain professional and authoritative.
"""

DEFAULT_GLOSSARY = [
    {
        "term": "Gross Margin",
        "definition": "Gross Profit divided by Total Revenue expressed as a percentage. Benchmark is > 55%.",
    },
    {
        "term": "AOV",
        "definition": "Average Order Value: Total Revenue divided by Total Order Count ($2.9K in Superstore).",
    },
    {
        "term": "Customer Segments",
        "definition": "Enterprise ($1.5M+ spend), Mid-Market ($500K-$1.5M spend), and SMB (<$500K spend).",
    },
    {
        "term": "Fiscal Year",
        "definition": "Standard calendar year ending December 31st.",
    },
    {
        "term": "Direct Sales",
        "definition": "Enterprise account executive closed revenue pipeline.",
    },
]

PRESETS: list[dict[str, Any]] = [
    {
        "id": "executive-c-suite",
        "name": "Voxora Executive Copilot",
        "avatar": "VX",
        "role_title": "Chief Analytics Officer",
        "description": "Strategic C-suite intelligence advisor synthesizing metrics into decisive executive briefings.",
        "tone": "executive",
        "temperature": 0.2,
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "greeting_message": "Good day. I am your Voxora Executive Copilot. What business metrics, revenue figures, or market insights shall we explore today?",
        "fallback_message": "I am focused exclusively on business intelligence, market trends, and organizational data. Please refine your inquiry around operational or financial metrics.",
        "voice_id": "en-US-Journey-F",
        "voice_speed": 1.0,
        "voice_pitch": 0.0,
        "allowed_data_areas": ["Revenue & Finance", "Product Performance", "Customer Intelligence", "Regional Operations"],
        "data_access_rules": {"mask_pii": True, "read_only": True, "auto_visualize": True, "allow_sql_generation": True},
        "knowledge_glossary": DEFAULT_GLOSSARY,
    },
    {
        "id": "financial-sleuth",
        "name": "Financial Sleuth & SQL Auditor",
        "avatar": "FA",
        "role_title": "Principal Financial Analyst",
        "description": "Granular financial analyst specializing in variance analysis, unit economics, and margin attribution.",
        "tone": "analytical",
        "temperature": 0.1,
        "system_prompt": """You are the Principal Financial Analyst for Voxora AI.
Analyze all queries with meticulous numerical rigor.
Always report variances, percentages to the decimal point, gross margins, and contribution margins.
When answering, structure your output into:
1. Exact Quantitative Summary
2. Variance Breakdown (YoY / MoM)
3. Risk & Exposure Analysis
Avoid fluff; prioritize statistical precision.""",
        "greeting_message": "Financial Analyst online. Ready to inspect revenue cohorts, cost variances, or SQL performance logs.",
        "fallback_message": "Request out of financial scope. Please specify a metric, financial statement line, or dataset entity.",
        "voice_id": "en-US-Journey-D",
        "voice_speed": 1.05,
        "voice_pitch": -1.0,
        "allowed_data_areas": ["Revenue & Finance", "Product Performance"],
        "data_access_rules": {"mask_pii": True, "read_only": True, "auto_visualize": True, "allow_sql_generation": True},
        "knowledge_glossary": DEFAULT_GLOSSARY + [
            {"term": "EBITDA Margin", "definition": "Operating earnings before interest, tax, depreciation, and amortization divided by revenue."},
            {"term": "Burn Rate", "definition": "Monthly net cash outflow from operations."},
        ],
    },
    {
        "id": "growth-strategist",
        "name": "Growth & Market Strategist",
        "avatar": "GS",
        "role_title": "VP of Revenue & Strategy",
        "description": "Forward-looking strategic advisor connecting data insights to market expansion and growth opportunities.",
        "tone": "strategic",
        "temperature": 0.4,
        "system_prompt": """You are the VP of Revenue & Strategy for Voxora AI.
Interpret every business query through the lens of growth, market share, and revenue expansion.
For every metric discussed:
1. Identify the growth catalyst or bottleneck.
2. Recommend high-ROI initiatives to capitalize on the trend.
3. Frame numbers in terms of competitive market dynamics.""",
        "greeting_message": "Welcome. Let's analyze where our highest-leverage growth opportunities and revenue expansions lie.",
        "fallback_message": "Let's focus on high-impact strategic queries. What market or revenue growth opportunity are you evaluating?",
        "voice_id": "en-US-Neural2-F",
        "voice_speed": 1.0,
        "voice_pitch": 1.0,
        "allowed_data_areas": ["Revenue & Finance", "Product Performance", "Customer Intelligence"],
        "data_access_rules": {"mask_pii": True, "read_only": True, "auto_visualize": True, "allow_sql_generation": True},
        "knowledge_glossary": DEFAULT_GLOSSARY + [
            {"term": "CAC", "definition": "Customer Acquisition Cost: Total sales & marketing expenditure divided by new customers acquired."},
            {"term": "LTV:CAC", "definition": "Ratio of Customer Lifetime Value to Customer Acquisition Cost. Ideal target > 3.0x."},
        ],
    },
    {
        "id": "technical-sql-specialist",
        "name": "Data Engineering Copilot",
        "avatar": "DE",
        "role_title": "Lead Data Architect",
        "description": "Technical data specialist providing exact BigQuery SQL syntax, schema mappings, and query optimization tips.",
        "tone": "technical",
        "temperature": 0.1,
        "system_prompt": """You are the Lead Data Architect for Voxora AI.
Provide clean, optimized Google BigQuery SQL queries, explain partitioning/clustering benefits, and detail data lineage.
Format SQL in code fences with uppercase keywords. Include execution tips and schema explanations.""",
        "greeting_message": "Data Architecture Copilot ready. Let's inspect BigQuery schemas, query efficiency, or data pipeline transformations.",
        "fallback_message": "Please supply a schema question, SQL query requirement, or data pipeline optimization task.",
        "voice_id": "en-US-Neural2-D",
        "voice_speed": 1.1,
        "voice_pitch": 0.0,
        "allowed_data_areas": ["Revenue & Finance", "Product Performance", "Customer Intelligence", "Regional Operations"],
        "data_access_rules": {"mask_pii": True, "read_only": True, "auto_visualize": True, "allow_sql_generation": True},
        "knowledge_glossary": DEFAULT_GLOSSARY + [
            {"term": "Slot Milliseconds", "definition": "Total compute time consumed by BigQuery worker slots during query execution."},
            {"term": "Partition Pruning", "definition": "BigQuery optimization skipping unneeded partition segments based on WHERE filters."},
        ],
    },
]


class AgentStudioService:
    """Service handling Agent Studio configurations and execution."""

    def get_presets(self) -> list[AgentPreset]:
        """Return all available pre-configured agent personas."""
        presets = []
        for p in PRESETS:
            glossary = [GlossaryItem(**g) for g in p["knowledge_glossary"]]
            presets.append(AgentPreset(**{**p, "knowledge_glossary": glossary}))
        return presets

    async def get_or_create_config(
        self,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> AgentConfig:
        """Fetch active agent configuration for tenant or initialize default."""
        query = select(AgentConfig).where(AgentConfig.tenant_id == tenant_id)
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            default_preset = PRESETS[0]
            config = AgentConfig(
                tenant_id=tenant_id,
                name=default_preset["name"],
                avatar=default_preset["avatar"],
                role_title=default_preset["role_title"],
                description=default_preset["description"],
                tone=default_preset["tone"],
                temperature=default_preset["temperature"],
                system_prompt=default_preset["system_prompt"],
                greeting_message=default_preset["greeting_message"],
                fallback_message=default_preset["fallback_message"],
                voice_id=default_preset["voice_id"],
                voice_speed=default_preset["voice_speed"],
                voice_pitch=default_preset["voice_pitch"],
                allowed_data_areas=default_preset["allowed_data_areas"],
                data_access_rules=default_preset["data_access_rules"],
                knowledge_glossary=default_preset["knowledge_glossary"],
                is_active=True,
            )
            db.add(config)
            await db.flush()

        return config

    async def update_config(
        self,
        tenant_id: UUID,
        update_data: AgentConfigUpdate,
        db: AsyncSession,
    ) -> AgentConfig:
        """Update existing tenant agent configuration."""
        config = await self.get_or_create_config(tenant_id, db)

        for key, value in update_data.model_dump(exclude_unset=True).items():
            if key == "knowledge_glossary" and value is not None:
                # Convert list of GlossaryItem or dicts to raw json list
                serialized = [item if isinstance(item, dict) else item.model_dump() for item in value]
                setattr(config, key, serialized)
            else:
                setattr(config, key, value)

        await db.flush()
        return config

    async def reset_config(
        self,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> AgentConfig:
        """Reset agent config to the factory default preset."""
        config = await self.get_or_create_config(tenant_id, db)
        default_preset = PRESETS[0]

        config.name = default_preset["name"]
        config.avatar = default_preset["avatar"]
        config.role_title = default_preset["role_title"]
        config.description = default_preset["description"]
        config.tone = default_preset["tone"]
        config.temperature = default_preset["temperature"]
        config.system_prompt = default_preset["system_prompt"]
        config.greeting_message = default_preset["greeting_message"]
        config.fallback_message = default_preset["fallback_message"]
        config.voice_id = default_preset["voice_id"]
        config.voice_speed = default_preset["voice_speed"]
        config.voice_pitch = default_preset["voice_pitch"]
        config.allowed_data_areas = default_preset["allowed_data_areas"]
        config.data_access_rules = default_preset["data_access_rules"]
        config.knowledge_glossary = default_preset["knowledge_glossary"]
        config.is_active = True

        await db.flush()
        return config

    def build_effective_system_prompt(self, config: AgentConfig | dict[str, Any]) -> str:
        """Combine persona, tone guidelines, and business glossary into a unified prompt."""
        if isinstance(config, AgentConfig):
            base_prompt = config.system_prompt
            tone = config.tone
            glossary = config.knowledge_glossary or []
            role = config.role_title
        else:
            base_prompt = config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
            tone = config.get("tone", "executive")
            glossary = config.get("knowledge_glossary", [])
            role = config.get("role_title", "Chief Analytics Officer")

        tone_instructions = {
            "executive": "Tone: Executive & Decisive. Lead with high-impact conclusions in bold, highlight gross revenue and margin takeaways, and use concise bullet points.",
            "analytical": "Tone: Deep Analytical & Rigorous. Focus on exact percentages, variance attribution, statistical cohorts, and financial margin analysis.",
            "strategic": "Tone: Strategic & Expansionist. Highlight growth vectors, competitive market positioning, and high-ROI expansion recommendations.",
            "technical": "Tone: Technical & Schema-Driven. Provide detailed SQL considerations, schema column references, and execution architecture notes.",
        }.get(tone, "Tone: Professional and data-backed.")

        glossary_text = ""
        if glossary:
            terms = "\n".join([f"- **{g.get('term') if isinstance(g, dict) else g.term}**: {g.get('definition') if isinstance(g, dict) else g.definition}" for g in glossary[:10]])
            glossary_text = f"\n\nCompany Business Glossary & Metric Definitions:\n{terms}"

        return f"{base_prompt}\n\nRole: {role}\n{tone_instructions}{glossary_text}"

    async def run_test_bench(self, request: AgentTestRequest) -> AgentTestResponse:
        """Execute a prompt against the draft agent configuration in the test sandbox."""
        start_time = time.time()

        system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT
        tone = request.tone or "executive"

        effective_prompt = self.build_effective_system_prompt({
            "system_prompt": system_prompt,
            "tone": tone,
            "knowledge_glossary": request.knowledge_glossary or [],
            "role_title": "Custom Agent Sandbox",
        })

        messages = [
            {"role": "user", "content": request.question}
        ]

        try:
            response_text, provider = await llm_service.generate_response(
                messages=messages,
                system_prompt=effective_prompt,
            )
        except Exception as e:
            logger.error("Sandbox test error: %s", e)
            response_text = "Error: Failed to generate response from the analytics engine. Please check your configuration and try again."
            provider = "error"

        latency = int((time.time() - start_time) * 1000)

        return AgentTestResponse(
            response=response_text,
            persona_applied="Custom Studio Sandbox",
            tone_applied=tone,
            model_used=provider,
            latency_ms=latency,
        )


agent_studio_service = AgentStudioService()
