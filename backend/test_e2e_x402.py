import asyncio
import base64
import sys
import httpx
from pydantic import BaseModel
from app.core.config import settings

def main():
    print("PHASE 1 - WALLET VERIFICATION")
    wallet_phrase = settings.APP_WALLET_PASSPHRASE or settings.APP_WALLET_MNEMONIC
    if not wallet_phrase:
        print("FAIL: No wallet phrase")
        sys.exit(1)
        
    try:
        from mnemonic import Mnemonic
        from slip10 import SLIP10
        import nacl.signing
        import algosdk
        
        mnemo = Mnemonic("english")
        seed_bytes = mnemo.to_seed(wallet_phrase)
        node = SLIP10.from_seed(seed_bytes, curve_name='ed25519')
        private_key_seed = node.get_privkey_from_path("m/44'/283'/0'/0'/0'")
        signing_key = nacl.signing.SigningKey(private_key_seed)
        verifying_key = signing_key.verify_key
        algo_sk = base64.b64encode(private_key_seed + bytes(verifying_key)).decode('utf-8')
        algo_addr = algosdk.account.address_from_private_key(algo_sk)
        
        expected_addr = "AYS4OQ2FSOQN3AVPM5T2YYZTF6K4DOOD56W3UI6PC2TPNVHTIMHK2X6A6U"
        print(f"Address derived: {algo_addr}")
        if algo_addr != expected_addr:
            print("Correct signer address: FAIL")
        else:
            print("Correct signer address: PASS")
            
        algod_client = algosdk.v2client.algod.AlgodClient("", settings.ALGOD_TESTNET_URL)
        account_info = algod_client.account_info(algo_addr)
        algo_balance = account_info.get('amount', 0) / 1_000_000
        print(f"ALGO Balance: {algo_balance}")
        
        asset_id = settings.ALGORAND_USDC_ASSET_ID
        assets = account_info.get('assets', [])
        opted_in = any(a['asset-id'] == asset_id for a in assets)
        print(f"USDC Opt-In: {opted_in}")
        usdc_balance = 0
        if opted_in:
            asset_info = next(a for a in assets if a['asset-id'] == asset_id)
            usdc_balance = asset_info.get('amount', 0) / 1_000_000
        print(f"USDC Balance: {usdc_balance}")
        
    except Exception as e:
        print(f"Error in Phase 1: {e}")
        
    print("\nPHASE 2 - x402 PAYMENT CHALLENGE")
    # We will simulate the frontend flow.
    import x402
    from x402.http import x402HTTPClient
    from x402 import x402Client
    from x402.mechanisms.avm.exact.client import ExactAvmScheme, ClientAvmSigner
    
    # We need to run this part asynchronously.
    # Actually, we can use the python requests library with the x402-python sdk.
    # We will just write an async test function.

async def async_test():
    try:
        from x402.http import HTTPFacilitatorClient, FacilitatorConfig
        from x402 import x402Client
        from x402.mechanisms.avm.exact.client import ExactAvmScheme, ClientAvmSigner
        
        # 1. Start by calling the endpoint directly using requests to get 402
        url = "http://localhost:8000/api/analysis/1"
        response = httpx.get(url)
        print(f"Initial GET Status: {response.status_code}")
        if response.status_code != 402:
            print("Failed to get 402 challenge")
            return
            
        print("402 Challenge headers:", response.headers)
        
        # We need a signer
        class DemoSigner(ClientAvmSigner):
            def __init__(self, sk):
                import algosdk
                self.sk = sk
                self._address = algosdk.account.address_from_private_key(sk)
                
            @property
            def address(self):
                return self._address
            
            def sign_transactions(self, txns, indexes_to_sign=None):
                import algosdk
                import base64
                signed = []
                for i, txn_bytes in enumerate(txns):
                    if indexes_to_sign and i not in indexes_to_sign:
                        signed.append(None)
                        continue
                    
                    txn = algosdk.transaction.Transaction.undictify(algosdk.encoding.msgpack.unpackb(txn_bytes))
                    signed_txn = txn.sign(self.sk)
                    signed.append(algosdk.encoding.msgpack.packb(signed_txn.dictify()))
                return signed
                
        # To get algo_sk:
        wallet_phrase = settings.APP_WALLET_PASSPHRASE or settings.APP_WALLET_MNEMONIC
        from mnemonic import Mnemonic
        from slip10 import SLIP10
        import nacl.signing
        import base64
        mnemo = Mnemonic("english")
        seed_bytes = mnemo.to_seed(wallet_phrase)
        node = SLIP10.from_seed(seed_bytes, curve_name='ed25519')
        private_key_seed = node.get_privkey_from_path("m/44'/283'/0'/0'/0'")
        signing_key = nacl.signing.SigningKey(private_key_seed)
        verifying_key = signing_key.verify_key
        algo_sk = base64.b64encode(private_key_seed + bytes(verifying_key)).decode('utf-8')

        signer = DemoSigner(algo_sk)
        
        base_client = x402Client()
        base_client.set_spend_controls(False)
        base_client.register("algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=", ExactAvmScheme(signer))
        
        # x402HTTPClient is not directly available in x402 python SDK like it is in TS.
        # Python SDK provides a parse_payment_required_header
        from x402 import parse_payment_required
        
        import json
        import base64
        www_auth = response.headers.get("payment-required")
        # Ensure padding is correct for base64 decode
        padding = '=' * (4 - (len(www_auth) % 4))
        decoded_header = base64.b64decode(www_auth + padding).decode('utf-8')
        decoded_header = decoded_header.replace('"paymentFlow":"standard"', '"paymentFlow":"authorization"')
        reqs = parse_payment_required(json.loads(decoded_header))
        
        print("Payment Requirements:")
        for r in reqs:
            print(f"Requirement: {r}")
            
        print("\nPHASE 3 - REAL PAYMENT")
        # Proceed with payment
        from x402.http import HTTPFacilitatorClient
        
        payload = await base_client.create_payment_payload(reqs)
        
        print("\nPHASE 4 - FACILITATOR VERIFICATION + SETTLEMENT")
        print(f"Payment Payload: {payload}")
        
        from x402.http import HTTPFacilitatorClient, FacilitatorConfig
        facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=settings.X402_FACILITATOR_URL))
        print("Settling payment with facilitator...")
        settled_payload = await facilitator.settle(payload, reqs)
        print("Payment settled successfully.")
        
        import base64
        payment_header = base64.urlsafe_b64encode(settled_payload.model_dump_json(exclude_none=True).encode('utf-8')).decode('utf-8')
        
        print("\nPHASE 6 - PAID REQUEST")
        res2 = httpx.get(url, headers={"x-402-payment": payment_header}, timeout=30.0)
        print(f"Paid GET Status: {res2.status_code}")
        try:
            print(f"Paid GET Response: {res2.json()}")
        except:
            print(f"Paid GET Response: {res2.text}")
            
    except Exception as e:
        print(f"Error in async test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    asyncio.run(async_test())
