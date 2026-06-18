import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List

class Base(DeclarativeBase):
    pass

class Monitor(Base):
    __tablename__ = "monitors"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    check_interval_seconds: Mapped[int] = mapped_column(Integer, default=120)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    results: Mapped[List["CheckResult"]] = relationship("CheckResult", back_populates="monitor", cascade="all, delete")
    incidents: Mapped[List["Incident"]] = relationship("Incident", back_populates="monitor", cascade="all, delete")

class CheckResult(Base):
    __tablename__ = "check_results"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    monitor_id: Mapped[str] = mapped_column(String, ForeignKey("monitors.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # "up" or "down"
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status_code: Mapped[int] = mapped_column(Integer, nullable=True)
    
    monitor: Mapped["Monitor"] = relationship("Monitor", back_populates="results")

class Incident(Base):
    __tablename__ = "incidents"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    monitor_id: Mapped[str] = mapped_column(String, ForeignKey("monitors.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    monitor: Mapped["Monitor"] = relationship("Monitor", back_populates="incidents")
