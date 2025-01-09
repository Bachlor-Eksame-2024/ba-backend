from fastapi import APIRouter, HTTPException, Depends, Request, Header, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, get_api_key
from authentication.jwt import get_current_user
from models import StripePayment
from datetime import datetime
import stripe
import os
from typing import Optional
from csrf import validate_csrf


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
payments_router = APIRouter()



class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "DKK"
    user_id: int
    payment_method: str = "card"


@payments_router.post(
    "/create-payment",
    dependencies=[Depends(get_api_key)],
    dependencies=[Depends(get_current_user)],
)
async def create_payment_intent(
    request: PaymentIntentRequest, db: Session = Depends(get_db)
):
    try:
        # Create Stripe PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency.lower(),
            payment_method_types=["card"],
            metadata={
                "user_id": str(request.user_id),
            },
        )

        # Store payment intent in database
        db_payment = StripePayment(
            user_id=request.user_id,
            payment_intent_id=intent.id,
            amount=request.amount,
            currency=request.currency,
            status="pending",
            payment_method=request.payment_method,
            created_at=datetime.utcnow(),
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
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Stripe signature is required")

    try:
        # Get the raw body
        payload = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, os.getenv("STRIPE_WEBHOOK_SECRET")
            )
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Handle the event
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
                payment.updated_at = datetime.utcnow()
                db.commit()

                return {
                    "status": "success",
                    "message": "Payment processed successfully",
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Payment with intent ID {payment_intent.id} not found",
                )

        # Handle other event types if needed
        return {"status": "success", "message": f"Unhandled event type {event.type}"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@payments_router.post("/webhook2")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Stripe signature is required")

    try:
        # Get the raw body
        payload = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, os.getenv("STRIPE_WEBHOOK_SECRET")
            )
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Handle the event
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
                payment.updated_at = datetime.utcnow()
                db.commit()

                return {
                    "status": "success",
                    "message": "Payment processed successfully",
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Payment with intent ID {payment_intent.id} not found",
                )

        # Handle other event types if needed
        return {"status": "success", "message": f"Unhandled event type {event.type}"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@payments_router.post("/webhook3")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Stripe signature is required")

    try:
        # Get the raw body
        payload = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, os.getenv("STRIPE_WEBHOOK_SECRET")
            )
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Handle the event
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
                payment.updated_at = datetime.utcnow()
                db.commit()

                return {
                    "status": "success",
                    "message": "Payment processed successfully",
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Payment with intent ID {payment_intent.id} not found",
                )

        # Handle other event types if needed
        return {"status": "success", "message": f"Unhandled event type {event.type}"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@payments_router.get("/{user_id}",dependencies=[Depends(get_api_key)],
    dependencies=[Depends(get_current_user)],)

async def get_user_payments(
    user_id: str = Path(..., description="The ID of the user"), db: Session = Depends(get_db)
):
    try:
        # Get user_id from current user
        user_id 

        # Query payments for user
        payments = (
            db.query(StripePayment)
            .filter(StripePayment.user_id == user_id)
            .order_by(StripePayment.created_at.desc())
            .all()
        )

        # Format payment data
        payment_list = []
        for payment in payments:
            payment_list.append(
                {
                    "payment_id": payment.payment_id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status,
                    "payment_intent_id": payment.payment_intent_id,
                    "created_at": payment.created_at.isoformat(),
                    "updated_at": (
                        payment.updated_at.isoformat() if payment.updated_at else None
                    ),
                }
            )

        return {"status": "success", "payments": payment_list}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching payments: {str(e)}"
        )
