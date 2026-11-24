"""
The four tables.

    groups          one row per group; the id is the secret token in the shareable link
    members         the people in a group (just a name, plus an optional UPI ID)
    expenses        one row per bill: who paid, how much, and how it was split
    expense_shares  one row per person per bill: how much of that bill is theirs

All money columns are PAISE (whole numbers).

Why save the shares instead of recomputing them? A bill split equally among 3 people
has uneven paise (3334 / 3333 / 3333). If we re-did the split later and the rule
ever changed, old bills would silently change. Stored shares never change.

Why never delete expenses? Deleting a bill only sets `deleted_at`. The row stays, so
the usage counter ("expenses created") stays truthful.
"""

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def now():
    return datetime.now(UTC)


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=now)

    members: Mapped[list["Member"]] = relationship(order_by="Member.id")


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    name: Mapped[str] = mapped_column(String(40))
    upi_id: Mapped[str | None] = mapped_column(String(100), default=None)


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    description: Mapped[str] = mapped_column(String(80))
    paid_by: Mapped[int] = mapped_column(ForeignKey("members.id"))
    amount_paise: Mapped[int]
    split_type: Mapped[str] = mapped_column(String(10))  # "equal" or "exact"
    created_at: Mapped[datetime] = mapped_column(default=now)
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    shares: Mapped[list["ExpenseShare"]] = relationship(order_by="ExpenseShare.id")


class ExpenseShare(Base):
    __tablename__ = "expense_shares"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    share_paise: Mapped[int]
