"""
Voxora Backend — Model registry.

Import all models here so Alembic and the app can discover them.
"""

from app.models.base import Base
from app.models.conversation import Conversation, Message, QueryLog, Visualization
from app.models.role import BusinessArea, Permission, Role
from app.models.tenant import Tenant
from app.models.user import User

__all__ = [
    "Base",
    "Tenant",
    "User",
    "Role",
    "Permission",
    "BusinessArea",
    "Conversation",
    "Message",
    "Visualization",
    "QueryLog",
]
