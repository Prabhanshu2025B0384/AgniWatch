from fastapi import APIRouter, Depends, Request
from app.services.x402_service import require_payment

router = APIRouter()

@router.get("/verify")
async def verify_payment(
    request: Request,
    payment_payload: dict = Depends(require_payment)
):
    """
    Endpoint protected by x402. 
    If a client calls this without payment, they get a 402 with requirements.
    If they provide a valid receipt, they get access.
    """
    return {
        "status": "success",
        "message": "Payment verified successfully",
        "protected_data": "This is highly confidential AI analysis.",
        "payload": payment_payload.model_dump()
    }
