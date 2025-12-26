from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db import Base

# Role ids and names:
ROLE_MAP = {
    1: ("🌱 Мл. модератор", "Junior Moderator"),
    2: ("🧩 Модератор", "Moderator"),
    3: ("🔰 Мл. администратор", "Junior Admin"),
    4: ("🛡 Администратор", "Admin"),
    5: ("👑 Владелец", "Owner"),
}


class Chat(Base):
    __tablename__ = "chats"
    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RoleAssignment(Base):
    __tablename__ = "role_assignments"
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    user_id = Column(BigInteger, index=True)
    role_id = Column(Integer, index=True)  # 1..5
    assigned_by = Column(BigInteger, nullable=True)
    reason = Column(Text, nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_chat_user_role"),
    )


class Nick(Base):
    __tablename__ = "nicks"
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    user_id = Column(BigInteger, index=True)
    nick = Column(String(64), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Warn(Base):
    __tablename__ = "warns"
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    user_id = Column(BigInteger, index=True)
    issued_by = Column(BigInteger, nullable=True)
    reason = Column(Text, nullable=True)
    until = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)