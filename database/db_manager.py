from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import sqlite3
from typing import Any

_SQLALCHEMY_AVAILABLE = False
try:
    from sqlalchemy import create_engine, select, text
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import sessionmaker

    from database.models import Base, Concept, ProblemHistory, User, UserProgress

    _SQLALCHEMY_AVAILABLE = True
except Exception:
    # SQLAlchemy may be partially installed in some runtimes; we'll fall back to sqlite3.
    _SQLALCHEMY_AVAILABLE = False

from config import get_settings


@dataclass
class AttemptRecord:
    concept_id: str
    problem_text: str
    correct: bool
    steps_taken: int
    time_spent_seconds: int
    user_solution: str


class DatabaseManager:
    """
    Lightweight DB abstraction used by the Streamlit app.
    Implemented fully in a later step; this file exists now for imports.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._engine = create_engine(
            self._settings.database_url,
            echo=False,
            connect_args={"check_same_thread": False}
            if self._settings.database_url.startswith("sqlite")
            else {},
        )
        self._SessionLocal = sessionmaker(bind=self._engine, expire_on_commit=False)
        self._problem_history_problem_column: str | None = None
        self.ensure_schema()

    def _get_problem_history_problem_column(self) -> str:
        """
        Handle historic DB schemas:
        - Old fallback schema used `problem` column.
        - Current ORM uses `problem_text`.
        """
        if self._problem_history_problem_column:
            return self._problem_history_problem_column

        # Default to the current ORM field.
        self._problem_history_problem_column = "problem_text"

        try:
            if not self._settings.database_url.startswith("sqlite"):
                return self._problem_history_problem_column

            with self._engine.connect() as conn:
                cols = conn.execute(text("PRAGMA table_info(problem_history)")).fetchall()
            col_names = {row[1] for row in cols}  # PRAGMA: (cid, name, type, ...)
            if "problem_text" in col_names:
                self._problem_history_problem_column = "problem_text"
            elif "problem" in col_names:
                self._problem_history_problem_column = "problem"
        except Exception:
            # If we can't inspect, keep the default.
            pass

        return self._problem_history_problem_column

    # --- Concept progress (placeholders) ---
    def get_or_create_user(self, username: str) -> int:
        with self._SessionLocal() as session:
            stmt = select(User).where(User.username == username)
            user = session.execute(stmt).scalar_one_or_none()
            if user is not None:
                return user.id

            user = User(username=username)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id

    def get_user_progress(self, user_id: int, concept_id: str) -> dict:
        with self._SessionLocal() as session:
            stmt = select(UserProgress).where(
                UserProgress.user_id == user_id, UserProgress.concept_id == concept_id
            )
            progress = session.execute(stmt).scalar_one_or_none()

            if progress is None:
                return {
                    "user_id": user_id,
                    "concept_id": concept_id,
                    "problems_attempted": 0,
                    "problems_correct": 0,
                    "mastery_level": 0.0,
                    "last_practiced": None,
                }

            return {
                "user_id": user_id,
                "concept_id": concept_id,
                "problems_attempted": progress.problems_attempted,
                "problems_correct": progress.problems_correct,
                "mastery_level": float(progress.mastery_level),
                "last_practiced": progress.last_practiced,
            }

    def upsert_progress(self, user_id: int, concept_id: str, correct: bool) -> None:
        now = datetime.utcnow()
        with self._SessionLocal() as session:
            stmt = select(UserProgress).where(
                UserProgress.user_id == user_id, UserProgress.concept_id == concept_id
            )
            progress = session.execute(stmt).scalar_one_or_none()

            if progress is None:
                progress = UserProgress(
                    user_id=user_id,
                    concept_id=concept_id,
                    problems_attempted=0,
                    problems_correct=0,
                    mastery_level=0.0,
                    last_practiced=now,
                )
                session.add(progress)

            progress.problems_attempted += 1
            progress.problems_correct += 1 if correct else 0
            progress.mastery_level = (
                100.0 * float(progress.problems_correct) / float(max(progress.problems_attempted, 1))
            )
            progress.last_practiced = now

            session.commit()

    # --- Problem history (placeholders) ---
    def record_attempt(self, user_id: int, record: AttemptRecord) -> None:
        problem_col = self._get_problem_history_problem_column()

        # If schema matches the ORM, use ORM to keep things simple.
        if problem_col == "problem_text":
            with self._SessionLocal() as session:
                history = ProblemHistory(
                    user_id=user_id,
                    concept_id=record.concept_id,
                    problem_text=record.problem_text,
                    user_solution=record.user_solution,
                    correct=record.correct,
                    steps_taken=record.steps_taken,
                    time_spent=record.time_spent_seconds,
                    timestamp=datetime.utcnow(),
                )
                session.add(history)
                session.commit()
        else:
            # Otherwise insert using raw SQL into the historic column name.
            with self._engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO problem_history
                        (user_id, concept_id, problem, user_solution, correct, steps_taken, time_spent, timestamp)
                        VALUES (:user_id, :concept_id, :problem, :user_solution, :correct, :steps_taken, :time_spent, :timestamp)
                        """
                    ),
                    {
                        "user_id": user_id,
                        "concept_id": record.concept_id,
                        "problem": record.problem_text,
                        "user_solution": record.user_solution,
                        "correct": 1 if record.correct else 0,
                        "steps_taken": int(record.steps_taken),
                        "time_spent": int(record.time_spent_seconds),
                        "timestamp": datetime.utcnow(),
                    },
                )

        # Update progress in a separate transaction
        self.upsert_progress(user_id=user_id, concept_id=record.concept_id, correct=record.correct)

    def get_recent_problem_texts(self, user_id: int, concept_id: str, limit: int) -> list[str]:
        problem_col = self._get_problem_history_problem_column()

        if problem_col == "problem_text":
            with self._SessionLocal() as session:
                stmt = (
                    select(ProblemHistory.problem_text)
                    .where(
                        ProblemHistory.user_id == user_id,
                        ProblemHistory.concept_id == concept_id,
                    )
                    .order_by(ProblemHistory.timestamp.desc())
                    .limit(limit)
                )
                rows = session.execute(stmt).all()
                return [r[0] for r in rows]

        # Historic fallback column: `problem`
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT problem
                    FROM problem_history
                    WHERE user_id = :user_id AND concept_id = :concept_id
                    ORDER BY timestamp DESC, id DESC
                    LIMIT :limit
                    """
                ),
                {"user_id": user_id, "concept_id": concept_id, "limit": int(limit)},
            ).fetchall()
        return [r[0] for r in rows]

    def get_recent_concepts(self, user_id: int, limit: int) -> list[str]:
        with self._SessionLocal() as session:
            # Order by most recent history timestamp per concept
            stmt = (
                select(ProblemHistory.concept_id, ProblemHistory.timestamp)
                .where(ProblemHistory.user_id == user_id)
                .order_by(ProblemHistory.timestamp.desc())
                .limit(limit * 5)
            )
            rows = session.execute(stmt).all()

            seen: set[str] = set()
            ordered: list[str] = []
            for concept_id, _ts in rows:
                if concept_id not in seen:
                    seen.add(concept_id)
                    ordered.append(concept_id)
                if len(ordered) >= limit:
                    break
            return ordered

    def get_all_user_progress(self, user_id: int) -> list[dict]:
        """
        Return progress rows for a user across all concepts.
        """
        with self._SessionLocal() as session:
            stmt = select(UserProgress).where(UserProgress.user_id == user_id)
            rows = session.execute(stmt).scalars().all()
            out: list[dict] = []
            for p in rows:
                out.append(
                    {
                        "user_id": p.user_id,
                        "concept_id": p.concept_id,
                        "problems_attempted": p.problems_attempted,
                        "problems_correct": p.problems_correct,
                        "mastery_level": float(p.mastery_level),
                        "last_practiced": p.last_practiced,
                    }
                )
            return out

    def ensure_schema(self) -> None:
        """Create tables if needed."""
        Base.metadata.create_all(bind=self._engine)

    def upsert_concepts(self, concepts: Iterable[tuple[str, Concept]]) -> None:
        """
        Ensure concepts exist in the DB (used on startup by the app).
        """
        with self._SessionLocal() as session:
            for _concept_id, concept in concepts:
                existing = session.get(Concept, concept.id)
                if existing is None:
                    session.add(concept)
                else:
                    existing.name = concept.name
                    existing.category = concept.category
                    existing.description = concept.description
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                # Re-try is not necessary; app will re-run and converge.


if not _SQLALCHEMY_AVAILABLE:
    class DatabaseManager:
        """
        sqlite3 fallback backend.

        This exists so the app can still run in environments where SQLAlchemy
        is partially installed/broken.
        """

        def __init__(self) -> None:
            self._settings = get_settings()

            db_url = self._settings.database_url
            db_path = "math_tutor.db"
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "", 1)
            elif db_url.startswith("sqlite://"):
                db_path = db_url.replace("sqlite://", "", 1)
            elif db_url.startswith("sqlite:"):
                db_path = db_url.replace("sqlite:", "", 1)

            # Relative paths are relative to the working directory (app root).
            if db_path and not db_path.startswith("/"):
                db_path = str(db_path)

            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self.ensure_schema()

        def ensure_schema(self) -> None:
            cur = self._conn.cursor()

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS concepts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    concept_id TEXT NOT NULL,
                    problems_attempted INTEGER NOT NULL DEFAULT 0,
                    problems_correct INTEGER NOT NULL DEFAULT 0,
                    mastery_level FLOAT NOT NULL DEFAULT 0.0,
                    last_practiced TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (concept_id) REFERENCES concepts(id),
                    UNIQUE(user_id, concept_id)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS problem_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    concept_id TEXT NOT NULL,
                    problem TEXT NOT NULL,
                    user_solution TEXT NOT NULL DEFAULT '',
                    correct INTEGER NOT NULL DEFAULT 0,
                    steps_taken INTEGER NOT NULL DEFAULT 0,
                    time_spent INTEGER NOT NULL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (concept_id) REFERENCES concepts(id)
                );
                """
            )

            self._conn.commit()

        def upsert_concepts(self, concepts: Iterable[tuple[str, Any]]) -> None:
            cur = self._conn.cursor()
            for _concept_id, concept in concepts:
                cur.execute(
                    """
                    INSERT INTO concepts (id, name, category, description)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        category=excluded.category,
                        description=excluded.description
                    """,
                    (concept.id, concept.name, concept.category, concept.description),
                )
            self._conn.commit()

        # --- Concept progress ---
        def get_or_create_user(self, username: str) -> int:
            cur = self._conn.cursor()
            row = cur.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if row is not None:
                return int(row["id"])
            cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
            self._conn.commit()
            return int(cur.lastrowid)

        def get_user_progress(self, user_id: int, concept_id: str) -> dict:
            cur = self._conn.cursor()
            row = cur.execute(
                """
                SELECT problems_attempted, problems_correct, mastery_level, last_practiced
                FROM user_progress
                WHERE user_id = ? AND concept_id = ?
                """,
                (user_id, concept_id),
            ).fetchone()
            if row is None:
                return {
                    "user_id": user_id,
                    "concept_id": concept_id,
                    "problems_attempted": 0,
                    "problems_correct": 0,
                    "mastery_level": 0.0,
                    "last_practiced": None,
                }
            return {
                "user_id": user_id,
                "concept_id": concept_id,
                "problems_attempted": int(row["problems_attempted"]),
                "problems_correct": int(row["problems_correct"]),
                "mastery_level": float(row["mastery_level"]),
                "last_practiced": row["last_practiced"],
            }

        def upsert_progress(self, user_id: int, concept_id: str, correct: bool) -> None:
            now = datetime.utcnow()
            cur = self._conn.cursor()
            row = cur.execute(
                """
                SELECT problems_attempted, problems_correct
                FROM user_progress
                WHERE user_id = ? AND concept_id = ?
                """,
                (user_id, concept_id),
            ).fetchone()

            if row is None:
                attempted = 1
                correct_count = 1 if correct else 0
                mastery = 100.0 * correct_count / max(attempted, 1)
                cur.execute(
                    """
                    INSERT INTO user_progress
                    (user_id, concept_id, problems_attempted, problems_correct, mastery_level, last_practiced)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, concept_id, attempted, correct_count, mastery, now),
                )
            else:
                attempted = int(row["problems_attempted"]) + 1
                correct_count = int(row["problems_correct"]) + (1 if correct else 0)
                mastery = 100.0 * correct_count / max(attempted, 1)
                cur.execute(
                    """
                    UPDATE user_progress
                    SET problems_attempted = ?, problems_correct = ?, mastery_level = ?, last_practiced = ?
                    WHERE user_id = ? AND concept_id = ?
                    """,
                    (attempted, correct_count, mastery, now, user_id, concept_id),
                )

            self._conn.commit()

        # --- Problem history ---
        def record_attempt(self, user_id: int, record: AttemptRecord) -> None:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO problem_history
                (user_id, concept_id, problem, user_solution, correct, steps_taken, time_spent, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    record.concept_id,
                    record.problem_text,
                    record.user_solution,
                    1 if record.correct else 0,
                    int(record.steps_taken),
                    int(record.time_spent_seconds),
                    datetime.utcnow(),
                ),
            )
            self._conn.commit()
            self.upsert_progress(user_id=user_id, concept_id=record.concept_id, correct=record.correct)

        def get_recent_problem_texts(self, user_id: int, concept_id: str, limit: int) -> list[str]:
            cur = self._conn.cursor()
            rows = cur.execute(
                """
                SELECT problem
                FROM problem_history
                WHERE user_id = ? AND concept_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (user_id, concept_id, int(limit)),
            ).fetchall()
            return [r["problem"] for r in rows]

        def get_recent_concepts(self, user_id: int, limit: int) -> list[str]:
            cur = self._conn.cursor()
            rows = cur.execute(
                """
                SELECT concept_id, timestamp
                FROM problem_history
                WHERE user_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (user_id, int(limit) * 5),
            ).fetchall()
            seen: set[str] = set()
            ordered: list[str] = []
            for r in rows:
                cid = r["concept_id"]
                if cid not in seen:
                    seen.add(cid)
                    ordered.append(cid)
                if len(ordered) >= limit:
                    break
            return ordered

        def get_all_user_progress(self, user_id: int) -> list[dict]:
            cur = self._conn.cursor()
            rows = cur.execute(
                """
                SELECT user_id, concept_id, problems_attempted, problems_correct, mastery_level, last_practiced
                FROM user_progress
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchall()
            out: list[dict] = []
            for r in rows:
                out.append(
                    {
                        "user_id": r["user_id"],
                        "concept_id": r["concept_id"],
                        "problems_attempted": int(r["problems_attempted"]),
                        "problems_correct": int(r["problems_correct"]),
                        "mastery_level": float(r["mastery_level"]),
                        "last_practiced": r["last_practiced"],
                    }
                )
            return out

