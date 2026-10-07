from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, select, text, update

from app.repositories.models import ComplaintRow
from app.schemas import Category, Complaint, Priority, Stats, Status


class ComplaintRepository:
    def __init__(self, sessions):
        self.sessions = sessions

    def ping(self) -> None:
        with self.sessions() as session:
            session.execute(text("SELECT 1"))

    def new_id(self) -> UUID:
        with self.sessions() as session:
            if session.bind.dialect.name == "postgresql":
                return session.scalar(select(func.gen_random_uuid()))
            return uuid4()  # SQLite unit tests only; production UUIDs come from Postgres.

    def create(self, values: dict) -> Complaint:
        with self.sessions.begin() as session:
            row = ComplaintRow(**values)
            session.add(row)
            session.flush()
            session.refresh(row)
            return Complaint.model_validate(row)

    def get(self, complaint_id: UUID) -> Complaint | None:
        with self.sessions() as session:
            row = session.get(ComplaintRow, complaint_id)
            return Complaint.model_validate(row) if row else None

    def list_complaints(
        self, page: int, page_size: int, category: Category | None, priority: Priority | None, status: Status | None
    ) -> tuple[list[Complaint], int]:
        conditions = [
            getattr(ComplaintRow, name) == value
            for name, value in {"category": category, "priority": priority, "status": status}.items()
            if value is not None
        ]
        with self.sessions() as session:
            # One snapshot: count and page remain consistent during concurrent writes.
            if session.bind.dialect.name == "postgresql":
                session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
            total = session.scalar(select(func.count()).select_from(ComplaintRow).where(*conditions)) or 0
            rows = session.scalars(
                select(ComplaintRow)
                .where(*conditions)
                .order_by(ComplaintRow.created_at.desc(), ComplaintRow.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            return [Complaint.model_validate(row) for row in rows], total

    def transition(self, complaint_id: UUID, expected: Status, target: Status) -> Complaint | None:
        with self.sessions.begin() as session:
            row = session.execute(
                update(ComplaintRow)
                .where(ComplaintRow.id == complaint_id, ComplaintRow.status == expected)
                .values(status=target, updated_at=func.now())
                .returning(ComplaintRow)
            ).scalar_one_or_none()
            return Complaint.model_validate(row) if row else None

    def stats(self) -> Stats:
        with self.sessions() as session:
            rows = session.execute(
                select(ComplaintRow.category, ComplaintRow.priority, ComplaintRow.status, func.count()).group_by(
                    ComplaintRow.category, ComplaintRow.priority, ComplaintRow.status
                )
            )
            result = Stats(
                total=0,
                by_category={v.value: 0 for v in Category},
                by_priority={v.value: 0 for v in Priority},
                by_status={v.value: 0 for v in Status},
            )
            for category, priority, status, count in rows:
                result.total += count
                result.by_category[category.value] += count
                result.by_priority[priority.value] += count
                result.by_status[status.value] += count
            return result

    def seed(self, rows: list[dict]) -> int:
        from sqlalchemy.dialects.postgresql import insert

        with self.sessions.begin() as session:
            if session.bind.dialect.name == "postgresql":
                result = session.execute(
                    insert(ComplaintRow)
                    .values(rows)
                    .on_conflict_do_nothing(index_elements=["id"])
                    .returning(ComplaintRow.id)
                )
                return len(result.all())
            count = 0
            for values in rows:
                if session.get(ComplaintRow, values["id"]) is None:
                    session.add(ComplaintRow(**values))
                    count += 1
            return count
