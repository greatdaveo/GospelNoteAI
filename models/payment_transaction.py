from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentTransactions(SQLModel, table=True):
    __tablename__ = "payment_transactions"
    
    id: Option[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    subscription_id: int = Field(foreign_key="user_subscriptions.id", index=True)
    stripe_payment_intent_id: str = Field(unique=True, index=True)
    stripe_change_id: Optional[str] = Field(default=None, index=True)
    amount: Decimal = Field(decimal_places=2)
    currency: str = Field(default="usd") # usd or eur 
    payment_method: Optional[str] = Field(defualt=None) # card or paypal
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)