from fastapi import APIRouter, HTTPException
from models.tenant import Tenant
from learning.perf_store import PerfStore
import stripe

router = APIRouter()

@router.post("/webhook")
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers['Stripe-Signature']
    endpoint_secret = 'your_stripe_webhook_secret'
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if event['type'] == 'invoice.payment_succeeded':
        tenant_id = event['data']['object']['customer']
        PerfStore.update_billing(tenant_id, event['data']['object']['amount_paid'])
    return {"received": True}

@router.get("/usage")
def get_usage(tenant_id: str):
    usage = PerfStore.get_usage(tenant_id)
    if not usage:
        raise HTTPException(status_code=404, detail="Usage not found")
    return usage