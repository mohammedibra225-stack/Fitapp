"""
Bases pour les fonctionnalites IA (regles 20 et 21) :

- Analyse d'un repas par photo -> MealPhotoAnalysis + items detectes.
  Une analyse IA est une ESTIMATION : l'utilisateur peut corriger
  chaque aliment/quantite detecte (is_confirmed / corrected_food_id).
- Assistant conversationnel -> Conversation + Message.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import AnalysisStatus, MessageRole

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.user import User


class MealPhotoAnalysis(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "meal_photo_analyses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Nullable : par choix (V1), la photo n'est pas persistee (envoyee
    # a Gemini en memoire uniquement). Rempli seulement si un stockage
    # (local/S3) est branche plus tard.
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status"), default=AnalysisStatus.PENDING
    )
    # Reponse brute du modele IA, conservee pour audit/debug/reentrainement
    raw_ai_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Lien optionnel vers le Meal cree une fois l'analyse confirmee
    resulting_meal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("meals.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship()
    items: Mapped[List["MealPhotoAnalysisItem"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class MealPhotoAnalysisItem(UUIDPKMixin, Base):
    """
    Un aliment detecte sur la photo. `is_confirmed_by_user` distingue
    la detection brute de la correction eventuelle de l'utilisateur
    (regle 20 : l'IA estime, l'utilisateur corrige).
    """

    __tablename__ = "meal_photo_analysis_items"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meal_photo_analyses.id", ondelete="CASCADE"),
        index=True,
    )

    # Detection brute par l'IA (peut ne pas matcher un Food existant)
    detected_label: Mapped[str] = mapped_column(String(150))
    matched_food_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("foods.id", ondelete="SET NULL"), nullable=True
    )
    estimated_portion: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    estimated_unit: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    estimated_calories_kcal: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    estimated_protein_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    estimated_carbs_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    estimated_fat_g: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True
    )

    is_confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    corrected_food_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("foods.id", ondelete="SET NULL"), nullable=True
    )
    corrected_portion: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2), nullable=True
    )

    analysis: Mapped["MealPhotoAnalysis"] = relationship(back_populates="items")
    matched_food: Mapped[Optional["Food"]] = relationship(foreign_keys=[matched_food_id])
    corrected_food: Mapped[Optional["Food"]] = relationship(
        foreign_keys=[corrected_food_id]
    )


class Conversation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(UUIDPKMixin, Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, name="message_role"))
    content: Mapped[str] = mapped_column(Text)
    language_code: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    # Contexte utilise par l'IA au moment de la reponse (objectifs,
    # nutrition du jour, etc.) -> utile pour debug/reproductibilite.
    context_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
