from fastapi import APIRouter
import stripe
import os 

stripe.api_key = os.getenv("STRIPE_API_KEY")
router = APIRouter()

@router.post("/api/stripe/create-checkout-session")
async def create_checkout_session(data: dict):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"{data['bits']} Bunny Bits Package",
                },
                "unit_amount": data["amount"],
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="https://parsebunnycli.com/success",
        cancel_url="https://yourdomain.com/cancel",
    )
    return {"id": session.id}
