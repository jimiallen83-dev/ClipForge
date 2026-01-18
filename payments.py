import os
from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/payments")

try:
    import stripe

    stripe.api_key = os.environ.get("STRIPE_API_KEY")
    _have_stripe = True
except Exception:
    stripe = None
    _have_stripe = False


@router.post("/create-checkout-session")
def create_checkout(user_id: int, tier: str = "creator"):
    if not _have_stripe:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    # In a real app we'd create a Stripe checkout session and return URL
    # Placeholder: return demo message
    return {"checkout_url": "https://checkout.stripe.dev/demo"}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    # Placeholder webhook receiver — validate signature in prod
    await request.body()
    # In production: parse event and update subscription records
    return {"status": "received"}
