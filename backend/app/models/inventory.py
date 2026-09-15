"""
Stock personnel de l'utilisateur : frigo, congelateur, placard
(regle 11).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import InventoryType, MeasurementUnit

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.user import User


class Inventory(UUIDPKMixin, TimestampMixin, Base):
    """Un "contenant" : le frigo de l'utilisateur, son placard, etc."""

    __tablename__ = "inventories"
    __table_args__ = (
        UniqueConstraint("user_id", "inventory_type", name="uq_user_inventory_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    inventory_type: Mapped[InventoryType] = mapped_column(
        Enum(InventoryType, name="inventory_type")
    )
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship(back_populates="inventories")
    items: Mapped[List["InventoryItem"]] = relationship(
        back_populates="inventory", cascade="all, delete-orphan"
    )


class InventoryItem(UUIDPKMixin, Base):
    __tablename__ = "inventory_items"

    inventory_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventories.id", ondelete="CASCADE"),
        index=True,
    )
    food_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("foods.id", ondelete="RESTRICT"), index=True
    )

    quantity: Mapped[float] = mapped_column(Numeric(7, 2))
    unit: Mapped[MeasurementUnit] = mapped_column(
        Enum(MeasurementUnit, name="inventory_measurement_unit")
    )

    added_on: Mapped[date] = mapped_column(Date)
    expires_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)

    inventory: Mapped["Inventory"] = relationship(back_populates="items")
    food: Mapped["Food"] = relationship()

    def __repr__(self) -> str:
        return f"<InventoryItem food_id={self.food_id} qty={self.quantity}{self.unit}>"
