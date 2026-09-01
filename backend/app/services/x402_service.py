from typing import Optional
from fastapi import Request, HTTPException
import json
import base64
from app.core.config import settings

from x402 import x402ResourceServer, ResourceConfig, parse_payment_payload
from x402.http import HTTPFacilitatorClient, FacilitatorConfig
from x402.mechanisms.avm.exact import ExactAvmServerScheme

# Initialize the facilitator client
facilitator_client = HTTPFacilitatorClient(
    FacilitatorConfig(url=settings.X402_FACILITATOR_URL)
)

# Initialize the resource server
x402_server = x402ResourceServer(facilitator_client)

ALGORAND_GENESIS_HASHES = {
    "testnet": "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
    "mainnet": "wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8="
}
algorand_network_id = ALGORAND_GENESIS_HASHES.get(settings.ALGORAND_NETWORK, settings.ALGORAND_NETWORK)
network_str = f"algorand:{algorand_network_id}"

# Monkey-patch ExactAvmScheme bug in x402 python SDK
from x402.mechanisms.avm.exact.server import ExactAvmScheme
if not hasattr(ExactAvmScheme, 'default_asset_transfer_method'):
    ExactAvmScheme.default_asset_transfer_method = 'axfer'
if not hasattr(ExactAvmScheme, 'payment_flows'):
    ExactAvmScheme.payment_flows = {
        'axfer': {
            'default': 'authorization',
            'supported': ['authorization']
        }
    }

x402_server.register(network_str, ExactAvmServerScheme())

async def init_x402():
    """Call this on startup to fetch supported kinds from facilitator"""
    x402_server.initialize()

from x402.schemas.base import AssetAmount

async def require_payment(request: Request):
    """
    FastAPI dependency that enforces x402 payment.
    Use this on endpoints that require payment.
    """
    x_payment = request.headers.get("payment-signature")
    
    # Calculate microUSDC
    try:
        price_microusdc = str(int(float(settings.X402_PRICE_USDC) * 1_000_000))
    except ValueError:
        price_microusdc = "50000" # Default 0.05 USDC

    asset_amount = AssetAmount(
        amount=price_microusdc, 
        asset=str(settings.ALGORAND_USDC_ASSET_ID), 
        extra={"decimals": 6}
    )

    def build_config():
        return ResourceConfig(
            scheme="exact",
            network=network_str,
            pay_to=settings.ALGORAND_RECEIVER_ADDRESS,
            price=asset_amount,
        )
    
    # If no payment header provided, return 402 with requirements
    if not x_payment:
        config = build_config()
        requirements = x402_server.build_payment_requirements(config)
        payment_required = await x402_server.create_payment_required_response(requirements)
        
        # Serialize to JSON and Base64 encode for header
        req_json = payment_required.model_dump_json()
        b64_req = base64.b64encode(req_json.encode()).decode()
        
        raise HTTPException(
            status_code=402,
            detail="Payment Required",
            headers={"payment-required": b64_req}
        )

    # Validate payment header
    try:
        # Decode base64 header
        payload_json = base64.urlsafe_b64decode(x_payment + '=' * (4 - len(x_payment) % 4)).decode()
        payload = parse_payment_payload(json.loads(payload_json))
        
        # We need to construct requirements again to verify
        config = build_config()
        requirements = x402_server.build_payment_requirements(config)
        matching_req = x402_server.find_matching_requirements(requirements, payload)
        
        if not matching_req:
            raise HTTPException(status_code=400, detail="Payment does not match requirements")

        # Verify payment with facilitator
        verify_result = await x402_server.verify_payment(payload, matching_req)
        
        if not verify_result.is_valid:
            reason = getattr(verify_result, 'model_dump_json', lambda: str(verify_result))()
            print(f"Payment Verification Failed: {reason}")
            raise HTTPException(status_code=402, detail=f"Payment Verification Failed: {reason}")
            
        # Optional: Can attach result to request state for downstream handlers
        request.state.payment_payload = payload
        return payload
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Invalid payment header: {str(e)}")
