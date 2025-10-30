from datetime import datetime
import uuid
from typing import Any, Dict, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    customer_name: Mapped[str] = mapped_column(db.String(80), nullable=False)
    status: Mapped[str] = mapped_column(
        db.String(20), nullable=False, default="received"
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.id,
            "customer_name": self.customer_name,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(db.String(80), nullable=False)
    quantity: Mapped[int] = mapped_column(db.Integer, nullable=False)
    order_id: Mapped[str] = mapped_column(
        db.String(36), db.ForeignKey("orders.id"), nullable=False
    )
    order: Mapped[Order] = relationship("Order", back_populates="items")

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.item_name, "quantity": self.quantity}
