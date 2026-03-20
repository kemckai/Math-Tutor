from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    progress: Mapped[list["UserProgress"]] = relationship(back_populates="user")
    history: Mapped[list["ProblemHistory"]] = relationship(back_populates="user")


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    progress: Mapped[list["UserProgress"]] = relationship(back_populates="concept")


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "concept_id", name="uq_user_concept"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    concept_id: Mapped[str] = mapped_column(String(64), ForeignKey("concepts.id"), index=True)

    problems_attempted: Mapped[int] = mapped_column(Integer, default=0)
    problems_correct: Mapped[int] = mapped_column(Integer, default=0)
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0)
    last_practiced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="progress")
    concept: Mapped["Concept"] = relationship(back_populates="progress")


class ProblemHistory(Base):
    __tablename__ = "problem_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    concept_id: Mapped[str] = mapped_column(String(64), ForeignKey("concepts.id"), index=True)

    problem_text: Mapped[str] = mapped_column(Text, nullable=False)
    user_solution: Mapped[str] = mapped_column(Text, nullable=False, default="")
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    steps_taken: Mapped[int] = mapped_column(Integer, default=0)
    time_spent: Mapped[int] = mapped_column(Integer, default=0)  # seconds
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="history")


