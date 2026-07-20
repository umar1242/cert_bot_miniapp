"""
db/models.py
Модели базы данных — удалены сущности планера и связанные с ним поля.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


# -------------------- основные модели (Quiz / Deck / etc) --------------------

class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int]       = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str]    = mapped_column(String(255), nullable=False, default="Без названия")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="quiz", cascade="all, delete-orphan",
        order_by="Question.position",
    )
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="quiz")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int]       = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int]  = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)   # порядок в квизе
    text: Mapped[str]     = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)  # о��ъяснение после ответа

    quiz: Mapped["Quiz"]                = relationship("Quiz", back_populates="questions")
    answers: Mapped[list["Answer"]]     = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan",
        order_by="Answer.position",
    )
    responses: Mapped[list["Response"]] = relationship(
        "Response", back_populates="question", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]    = mapped_column(Integer, nullable=False)
    text: Mapped[str]        = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    question: Mapped["Question"] = relationship("Question", back_populates="answers")


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class SessionMode(PyEnum):
    solo = "solo"
    group = "group"


class SessionStatus(PyEnum):
    waiting = "waiting"
    active = "active"
    finished = "finished"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    mode: Mapped[SessionMode]     = mapped_column(Enum(SessionMode), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), nullable=False, default=SessionStatus.waiting
    )

    current_question_idx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None]  = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # поле plan_item_id удалено вместе с планером

    quiz: Mapped["Quiz"]                    = relationship("Quiz", back_populates="sessions")
    participants: Mapped[list["SessionUser"]] = relationship(
        "SessionUser", back_populates="session", cascade="all, delete-orphan"
    )
    responses: Mapped[list["Response"]]     = relationship(
        "Response", back_populates="session", cascade="all, delete-orphan"
    )


class SessionUser(Base):
    __tablename__ = "session_users"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int]  = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="participants")


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    answer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="responses")
    question: Mapped["Question"] = relationship("Question", back_populates="responses")


# ---------------------------------------------------------------------------
# Deck / Cards
# ---------------------------------------------------------------------------

class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int]       = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str]    = mapped_column(String(255), nullable=False, default="Без названия")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    cards: Mapped[list["Card"]] = relationship(
        "Card", back_populates="deck", cascade="all, delete-orphan",
        order_by="Card.position",
    )


class Card(Base):
    """Одна флешкарта: лицо (front) и оборот (back)."""
    __tablename__ = "cards"

    id: Mapped[int]       = mapped_column(Integer, primary_key=True)
    deck_id: Mapped[int]  = mapped_column(ForeignKey("decks.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)   # порядок в колоде
    front: Mapped[str]    = mapped_column(Text, nullable=False)      # лицевая сторона
    back: Mapped[str]     = mapped_column(Text, nullable=False)      # правильный оборот (true)
    back_false: Mapped[str | None] = mapped_column(Text, nullable=True)  # ложный оборот для теста «Верно/Неверно"

    deck: Mapped["Deck"] = relationship("Deck", back_populates="cards")


# остальной код и модели остались без изменений
