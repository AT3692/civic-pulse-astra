from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, Integer, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.repositories.database import Base
from app.schemas import Category, Priority, Status


class ComplaintRow(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint("length(text) BETWEEN 10 AND 2000", name="ck_text_length"),
        CheckConstraint("length(location) BETWEEN 3 AND 200", name="ck_location_length"),
        CheckConstraint("triage_latency_ms >= 0", name="ck_latency"),
        Index("ix_complaints_status_priority", "status", "priority"),
        Index("ix_complaints_created_at", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    text: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(200))
    reporter_contact: Mapped[str | None] = mapped_column(String(254))
    category: Mapped[Category] = mapped_column(Enum(Category, name="category", create_constraint=True))
    priority: Mapped[Priority] = mapped_column(Enum(Priority, name="priority", create_constraint=True))
    status: Mapped[Status] = mapped_column(Enum(Status, name="status", create_constraint=True), server_default="open")
    ai_summary: Mapped[str | None] = mapped_column(String(140))
    triaged_by: Mapped[str] = mapped_column(String(40))
    triage_latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
