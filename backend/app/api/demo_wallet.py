from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import base64
import nacl.signing
from app.core.config import settings


router = APIRouter()

class SignRequest(BaseModel):
    unsigned_txn_b64: str

@router.post("/sign-payment")
async def sign_payment(req: SignRequest):
    """
    Demo Wallet Signer: Signs an Algorand transaction using the server-side Pera 24-word phrase.
    This simulates a user's wallet approving the x402 payment.
    """
    if not settings.APP_WALLET_PASSPHRASE:
        raise HTTPException(status_code=400, detail="Demo wallet passphrase not configured on server")
        
    try:
        from mnemonic import Mnemonic
        import slip10
        import algosdk
        
        # 1. Get the 512-bit seed from the 24-word phrase
        mnemo = Mnemonic("english")
        seed_bytes = mnemo.to_seed(settings.APP_WALLET_PASSPHRASE)
        
        # 2. Derive the key using SLIP-10 for Ed25519 using the Algorand path m/44'/283'/0'/0'/0'
        path = [
            slip10.harden(44),
            slip10.harden(283),
            slip10.harden(0),
            slip10.harden(0),
            slip10.harden(0)
        ]
        
        derived = slip10.derive(seed_bytes, path, slip10.Curve.ed25519)
        private_key_seed = derived[0]
        
        signing_key = nacl.signing.SigningKey(private_key_seed)
        verifying_key = signing_key.verify_key
        algo_sk = base64.b64encode(private_key_seed + bytes(verifying_key)).decode('utf-8')
        
        # Decode the msgpack Algorand transaction from base64
        txn_bytes = base64.b64decode(req.unsigned_txn_b64)
        
        # Note: In algosdk, to sign a transaction we typically parse it first
        # But x402 unsigned_txn_b64 is a msgpack encoded transaction.
        txn = algosdk.transaction.Transaction.undictify(algosdk.encoding.msgpack.unpackb(txn_bytes))
        
        # Sign it
        signed_txn = txn.sign(algo_sk)
        
        # Export back to base64
        signed_bytes = base64.b64encode(algosdk.encoding.msgpack.packb(signed_txn.dictify())).decode('utf-8')
        
        return {"signed_txn_b64": signed_bytes}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign transaction: {str(e)}")

@router.get("/address")
async def get_demo_address():
    if not settings.APP_WALLET_PASSPHRASE:
        raise HTTPException(status_code=400, detail="Demo wallet passphrase not configured on server")
    try:
        from mnemonic import Mnemonic
        import slip10
        
        # 1. Get the 512-bit seed from the 24-word phrase
        mnemo = Mnemonic("english")
        seed_bytes = mnemo.to_seed(settings.APP_WALLET_PASSPHRASE)
        
        # 2. Derive the key using SLIP-10 for Ed25519 using the Algorand path m/44'/283'/0'/0'/0'
        path = [
            slip10.harden(44),
            slip10.harden(283),
            slip10.harden(0),
            slip10.harden(0),
            slip10.harden(0)
        ]
        
        derived = slip10.derive(seed_bytes, path, slip10.Curve.ed25519)
        private_key_seed = derived[0]
        
        signing_key = nacl.signing.SigningKey(private_key_seed)
        verifying_key = signing_key.verify_key
        algo_sk = base64.b64encode(private_key_seed + bytes(verifying_key)).decode('utf-8')
        
        import algosdk
        algo_addr = algosdk.account.address_from_private_key(algo_sk)
        return {"address": algo_addr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to derive address: {str(e)}")
