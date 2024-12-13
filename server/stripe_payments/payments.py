from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import stripe
import os

# Initialize Stripe with the secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

payments_router = APIRouter()


class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "usd"


# Man skal være JWT verificeret for at kunne lave en betaling
@payments_router.post("/")
async def create_payment_intent(request: PaymentIntentRequest):
    try:
        # Create a payment intent with the specified amount and currency
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
        )
        return {"client_secret": intent.client_secret}
    except stripe.error.StripeError as e:
        # Handle Stripe errors
        raise HTTPException(status_code=400, detail=str(e))
