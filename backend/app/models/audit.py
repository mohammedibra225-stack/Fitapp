"""
Audit generique (regle 23).

Complement de `body_measurements` (deja insert-only pour le poids et
les mensurations) : `AuditLog` couvre les changements importants sur
n'importe quelle autre entite (ex: changement d'objectif, de niveau
sportif...) sans avoir a creer une table d'historique par champ.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(UUIDPKMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50))  # ex: "profile"
    entity_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True))
    field_name: Mapped[str] = mapped_column(String(50))
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.entity_type}.{self.field_name} at={self.changed_at}>"
