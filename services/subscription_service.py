from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Session, select
from models.user_subscription import UserSubscription, SubscriptionStatus
from models.subscription_plan import SubscriptionPlan
from models.usage_record import UsageRecord
import stripe

class SubscriptionService:
    def __init__(self, db: Session, stripe_secret_key: str):
        self.db = db
        stripe.api_key = stripe_secret_key

    def get_user_subscription(self, user_id: int) -> Optional[UserSubscription]:
        """Get user active subscription"""
        statement = select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == SubscriptionStatus.ACTIVE
        ).order_by(UserSubscription.created_at.desc)

        result = self.db.exec(statement).first()

        return result

    def create_subscription(
        self,
        user_id: int,
        plan_id: int,
        stripe_customer_id: str
    ) -> UserSubscription:
        """After payment create a new subscription for a user"""
        plan = self.db.get(SubscriptionPlan, plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # Calculate the billing period (monthly
        now = datetime.utcnow()
        period_end = now + timedelta(days=30)

        # Create subscription record
        subscription = UserSubscription(
            user_id = user_id,
            plan_id = plan_id,
            stripe_customer_id=stripe_customer_id,
            status = SubscriptionStatus.ACTIVE,
            current_period_start = now,
            current_period_end = period_end
        )

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

    def upgrade_subscription(
        self,
        user_id: int,
        new_plan_id: int
    ) -> UserSubscription:
        """Upgrade user subscription to a new plan"""
        # Get current subscription
        current_sub = self.get_user_subscription(user_id)
        if not current_sub:
            raise ValueError("User has no active subscription")

        # Get new plan
        new_plan = self.db.get(SubscriptionPlan, new_plan_id)
        if not new_plan:
            raise ValueError(f"Plan {new_plan_id} not found")

        # If upgrading to same or lower plan, return current
        if current_sub.plan_id == new_plan_id:
            return current_sub

        # Cancel current subscription
        current_sub.status = SubscriptionStatus.CANCELED
        current_sub.canceled_at = datetime.utcnow()

        new_subscription = UserSubscription(
            user_id = user_id,
            plan_id = new_plan_id,
            stripe_customer_id = current_sub.stripe_customer_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=period_end
        )

        self.db.add(new_subscription)
        self.db.commit()
        self.db.refresh(new_subscription)

        return new_subscription

    def cancel_subscription(self, user_id: int) -> UserSubscription:
        """
        Cancel user's subscription.
        """
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            raise ValueError("User has no active subscription")

        subscription.cancel_at_period_end = True
        subscription.canceled_at = datetime.utcnow()
        subscription.updated_at = datetime.utcnow()

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        return subscription

    def get_all_plans(self) -> list[SubscriptionPlan]:
        """Get all active subscription plans."""
        statement = select(SubscriptionPlan).where(
            SubscriptionPlan.is_active == True
        ).order_by(SubscriptionPlan.price_monthly)

        result = list(self.db.exec(statement).all())

        return result

    def sync_stripe_subscription(
        self,
        stripe_subscription_id: str,
        status: str
    ) -> Optional[UserSubscription]:
        """This sync subs status from Stripe webhook"""
        subscription = self.db.exec(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == stripe_subscription_id
            )
        ).first()

        if not subscription:
            return None

        # Map Stripe status to the status
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "canceled": SubscriptionStatus.CANCELED,
            "past_due": SubscriptionStatus.PAST_DUE,
            "trialing": SubscriptionStatus.TRIALING,
        }

        subscription.status = status_map(status, SubscriptionStatus.ACTIVE)
        subscription.updated_at = datetime.utcnow()

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        return subscription


