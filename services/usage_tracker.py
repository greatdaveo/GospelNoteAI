from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from sqlmodel import Session, select
from models.usage_record import UsageRecord
from models.user_subscription import UserSubscription, SubscriptionStatus
from models.subscription_plan import SubscriptionPlan

class UsageTracker:
    def __init__(self, db: Session):
        self.db = db

    def get_current_usage(self, user_id: int) -> Dict[str, Any]:
        """
        Get current usage for a user in the current month.
        """
        subscription = self._get_active_subscription(user_id)
        if not subscription:
            return self._get_default_usage()

        # Get current month usage record
        current_month = date.today().replace(day=1)
        usage_record = self._get_or_create_usage_record(user_id, subscription.id, current_month)

        # Get plan limits
        plan = self.db.get(SubscriptionPlan, subscription.plan_id)

        count_limit = plan.transcription_count_limit
        time_limit = plan.transcription_time_limit

        # Calculate remaining
        count_remaining = (
            count_limit - usage_record.transcription_count
            if count_limit > 0
            else float('inf')
        )
        time_remaining = time_limit - usage_record.transcription_duration_seconds

        can_transcribe = self._can_transcribe(
            usage_record.transcription_count,
            usage_record.transcription_duration_seconds,
            count_limit,
            time_limit
        )

        return {
            "transcription_count": usage_record.transcription_count,
            "transcription_duration_seconds": usage_record.transcription_duration_seconds,
            "count_limit": count_limit,
            "time_limit": time_limit,
            "count_remaining": max(0, int(count_remaining)) if count_remaining != float('inf') else -1,
            "time_remaining": max(0, time_remaining),
            "can_transcribe": can_transcribe,
            "subscription_status": subscription.status.value,
            "plan_name": plan.name
        }


    def can_user_transcribe(
        self,
        user_id: int,
        audio_duration_seconds: int
    ) -> tuple[bool, Optional[str]]:
        usage = self.get_current_usage(user_id)

        if not usage["can_transcribe"]:
            return False, "Monthly transcription limit reached"

        if usage["count_remaining"] == 0:
            return False, f"You have reached your monthly limit of {usage['count_limit']} transcriptions"

        if usage["time_remaining"] < audio_duration_seconds:
            remaining_minutes = usage["time_remaining"] # 60 limit
            return False, f"Insufficient time remaining. You have {remaining_minutes} minutes left"

        return True, None

    def record_transcription(
        self,
        user_id: int,
        audio_duration_seconds: int
    ) -> UsageRecord:
        subscription = self._get_active_subscription(user_id)

        if not  subscription:
            raise ValueError("User has no active subscription")



        return

    def _get_active_subscription(
        self,
        user_id: int
    ) -> Optional[UserSubscription]:
        statement = select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == SubscriptionStatus.ACTIVE
        ).order_by(UserSubscription.created_at_desc())

        result = self.db.exec(statement).first()

        return result

    def _get_or_create_usage_record(
        self,
        user_id: int,
        subscription_id: int,
        usage_month: date
    ):
        """Get or create usage record for a month"""
        statement = select(UsageRecord).where(
            UsageRecord.user_id == user_id,
            UserRecord.usage_month == usage_month
        )

        usage_record = self.db.exec(statement).first()

        if not usage_record:
            usage_record = UsageRecord(
                user_id = user_id,
                subscription_id = subscription_id,
                usage_month = usage_month,
                transcription_count = 0,
                transcription_duration_seconds = 0
            )

            self.db.add(usage_record)
            self.db.commit()
            self.db.refresh(usage_record)

        return usage_record

    def _can_transcribe(
        self,
        current_count: int,
        current_duration: int,
        count_limit: int,
        time_limit: int
    ) -> bool:
        """Check if user can transcribe based on limits"""
        # Check count limit (-1 means unlimited)
        if count_limit > 0 and current_count >= count_limit:
            return False

        # Check time limit
        if time_limit > 0 and current_duration >= time_limit:
            return False

        return True

    def _get_default_usage(self) -> Dict[str, Any]:
        """Default usage for users without subscription."""
        return {
            "transcription_count": 0,
            "transcription_duration_seconds": 0,
            "count_limit": 0,
            "time_limit": 0,
            "count_remaining": 0,
            "time_remaining": 0,
            "can_transcribe": False,
            "subscription_status": "none",
            "plan_name": "None"
        }

