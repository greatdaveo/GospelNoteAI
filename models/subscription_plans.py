from sqlmodel import SQLModel, Field
from tying import Optional, Dict, Any
from datetime import datetime
from sqlalcehmy import Column
from sqlalchemy.dialects.postgresql import JSONB

class SubscriptionPlan(SQLModel, table=True):
    __tablename__ = "subscription_plans"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True) # "Free", "Basic", "Pro"
    slug: str = Field(index=True, unique=True) # # "free", "basic", "pro"
    price_monthly: float = Field(default=0.0)
    transcription_time_limit: int = Field(default=0) # Total seconds per month
    transcription_count_limit: int = Field(default=0) # Number of transccriptions per months
    features: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB)
    )
    stripe_price_id: Optional[str] = Field(default=None, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory = datetime.utcnow)
    updated_at: datetime = Field(default_factory = datetime.utcnow)
