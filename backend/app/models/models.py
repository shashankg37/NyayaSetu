import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON
from app.db import Base

JSONBCompat = JSON().with_variant(__import__('sqlalchemy.dialects.postgresql', fromlist=['JSONB']).JSONB, 'postgresql')

class Role(str, enum.Enum): citizen='citizen'; csc_operator='csc_operator'; paralegal='paralegal'; admin='admin'
class InputType(str, enum.Enum): text='text'; voice='voice'; image='image'
class DraftStatus(str, enum.Enum): collecting='collecting'; ready='ready'; generated='generated'

class User(Base):
    __tablename__='users'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); email: Mapped[str]=mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str]=mapped_column(String(255)); role: Mapped[Role]=mapped_column(Enum(Role), default=Role.citizen)
    preferred_language: Mapped[str]=mapped_column(String(32), default='en'); consent_given: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class Session(Base):
    __tablename__='sessions'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); user_id: Mapped[int|None]=mapped_column(ForeignKey('users.id'), index=True, nullable=True)
    started_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow); sensitive_mode: Mapped[bool]=mapped_column(Boolean, default=False)

class Conversation(Base):
    __tablename__ = 'conversations'
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    user_id: Mapped[int|None] = mapped_column(ForeignKey('users.id'), index=True, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default='en')
    legal_domain: Mapped[str|None] = mapped_column(String(100))
    state_json: Mapped[dict] = mapped_column(JSONBCompat, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey('conversations.id'), index=True)
    role: Mapped[str] = mapped_column(String(50)) # 'user', 'ai', 'system'
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONBCompat, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Lawyer(Base):
    __tablename__ = 'lawyers'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    specialization: Mapped[str] = mapped_column(String(255))
    jurisdiction: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(255))
    district: Mapped[str] = mapped_column(String(255))
    languages: Mapped[list] = mapped_column(JSONBCompat, default=list)
    experience_years: Mapped[int] = mapped_column(Integer)
    fee_range: Mapped[str] = mapped_column(String(255))
    pro_bono: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    contact: Mapped[str] = mapped_column(String(255))

class Feedback(Base):
    __tablename__ = 'feedback'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int|None] = mapped_column(ForeignKey('users.id'), index=True, nullable=True)
    conversation_id: Mapped[str|None] = mapped_column(ForeignKey('conversations.id'), index=True, nullable=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str|None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LegalSourceMetadata(Base):
    __tablename__ = 'legal_source_metadata'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(1024))
    tier: Mapped[int] = mapped_column(Integer, default=3)
    last_ingested: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Query(Base):
    __tablename__='queries'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); session_id: Mapped[int]=mapped_column(ForeignKey('sessions.id'), index=True)
    raw_input_type: Mapped[InputType]=mapped_column(Enum(InputType)); raw_input_ref: Mapped[str]=mapped_column(Text)
    detected_language: Mapped[str|None]=mapped_column(String(32)); intent: Mapped[str|None]=mapped_column(String(100)); beneficiary_context: Mapped[str|None]=mapped_column(String(100))

class Response(Base):
    __tablename__='responses'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); query_id: Mapped[int]=mapped_column(ForeignKey('queries.id'), index=True)
    answer_payload: Mapped[dict]=mapped_column(JSONBCompat); confidence_score: Mapped[float|None]=mapped_column(Float); fallback_used: Mapped[bool]=mapped_column(Boolean, default=False); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class UploadedDocument(Base):
    __tablename__='documents_uploaded'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); session_id: Mapped[int]=mapped_column(ForeignKey('sessions.id'), index=True)
    original_filename: Mapped[str]=mapped_column(String(255)); storage_ref: Mapped[str]=mapped_column(String(500)); doc_type: Mapped[str|None]=mapped_column(String(100)); extracted_fields: Mapped[dict|None]=mapped_column(JSONBCompat); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class DraftedDocument(Base):
    __tablename__='drafted_documents'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); session_id: Mapped[int]=mapped_column(ForeignKey('sessions.id'), index=True)
    doc_type: Mapped[str]=mapped_column(String(100)); collected_fields: Mapped[dict]=mapped_column(JSONBCompat, default=dict); draft_status: Mapped[DraftStatus]=mapped_column(Enum(DraftStatus), default=DraftStatus.collecting); final_file_ref: Mapped[str|None]=mapped_column(String(500)); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class Timeline(Base):
    __tablename__='timelines'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); session_id: Mapped[int]=mapped_column(ForeignKey('sessions.id'), index=True); events: Mapped[list]=mapped_column(JSONBCompat); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__='audit_log'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); user_id: Mapped[int|None]=mapped_column(ForeignKey('users.id'), index=True, nullable=True); action: Mapped[str]=mapped_column(String(100)); resource_type: Mapped[str]=mapped_column(String(100)); resource_id: Mapped[str]=mapped_column(String(100)); timestamp: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
