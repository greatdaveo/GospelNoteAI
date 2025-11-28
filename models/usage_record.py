from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date
from sqlalchemy import UniqueConstraint

class UsageRecor(SQLModel, table=True):
    __tablename__ = "usage_records"

    # Composite unique constraint ensures one record per user per month
    __table_args__ = (
        UniqueConstraint("user_id", "usage_month", name="unique_user_month"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    subscription_id: int = Field(foreign_key="user_subscriptions.id", index=True)
    usage_month: date = Field(index=True)
    transcription_count: int = Field(default=0)
    transcription_duration_seconds: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
