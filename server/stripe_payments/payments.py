from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from authentication.jwt import get_current_user
from models import StripePayment
from datetime import datetime
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
payments_router = APIRouter(dependencies=[Depends(get_current_user)])


class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "DKK"
    user_id: int
    payment_method: str = "card"  # Can be 'card', 'link', or 'mobilepay'


@payments_router.post("/create-payment")
async def create_payment_intent(
    request: PaymentIntentRequest, db: Session = Depends(get_db)
):
    try:
        # Create Stripe PaymentIntent with specific payment methods
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            payment_method_types=["card", "link", "mobilepay"],  # Keep only this
            # Remove automatic_payment_methods
        )

        db_payment = StripePayment(
            user_id=request.user_id,
            payment_intent_id=intent.id,
            amount=request.amount,
            currency=request.currency,
            status=intent.status,
            payment_method=request.payment_method,
            created_at=datetime.now(),
        )

        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)

        return {
            "client_secret": intent.client_secret,
            "payment_id": db_payment.payment_id,
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@payments_router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )

        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            # Update payment status in database
            payment = (
                db.query(StripePayment)
                .filter(StripePayment.payment_intent_id == payment_intent.id)
                .first()
            )
            if payment:
                payment.status = "succeeded"
                db.commit()

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
