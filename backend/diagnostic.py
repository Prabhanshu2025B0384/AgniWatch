import asyncio
import os
import sys
import json
from pathlib import Path

# Add the app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.x402_service import x402_server
from algosdk.v2client import algod
import httpx

async def run_diagnostic():
    print("==================================================")
    print("X402 REAL TESTNET INTEGRATION DIAGNOSTIC")
    print("==================================================")
    
    issues = []
    
    # Check Network
    network = settings.ALGORAND_NETWORK
    print(f"[ ] Network = {network}")
    if network != "testnet":
        issues.append("WRONG_NETWORK: Network must be 'testnet'")
    else:
        print("[X] Network = testnet")

    # Check USDC Asset
    asset_id = settings.ALGORAND_USDC_ASSET_ID
    print(f"[ ] USDC asset ID = {asset_id}")
    if str(asset_id) != "10458941":
        issues.append("WRONG_ASSET: USDC Asset ID must be 10458941")
    else:
        print("[X] USDC asset ID = 10458941")

    # Check Payer/Receiver
    # For payer, we get the derived address
    try:
        # Payer derived in config.py
        import base64
        import nacl.signing
        import algosdk
        from slip10 import SLIP10
        from mnemonic import Mnemonic
        
        wallet_phrase = settings.APP_WALLET_MNEMONIC
        mnemo = Mnemonic("english")
        seed_bytes = mnemo.to_seed(wallet_phrase)
        node = SLIP10.from_seed(seed_bytes, curve_name='ed25519')
        private_key_seed = node.get_privkey_from_path("m/44'/283'/0'/0'/0'")
        signing_key = nacl.signing.SigningKey(private_key_seed)
        verifying_key = signing_key.verify_key
        algo_sk = base64.b64encode(private_key_seed + bytes(verifying_key)).decode('utf-8')
        payer_address = algosdk.account.address_from_private_key(algo_sk)
    except Exception as e:
        payer_address = None
        issues.append(f"WALLET_CONFIGURATION_ERROR: Failed to derive payer address - {e}")
        
    receiver_address = settings.ALGORAND_RECEIVER_ADDRESS
    
    print(f"[ ] Payer address = {payer_address}")
    if payer_address and algosdk.encoding.is_valid_address(payer_address):
        print(f"[X] Payer address is valid: {payer_address}")
    else:
        issues.append("INVALID_PAYER: Payer address is missing or invalid")
        
    print(f"[ ] Receiver address = {receiver_address}")
    if receiver_address and algosdk.encoding.is_valid_address(receiver_address):
        print(f"[X] Receiver address is valid: {receiver_address}")
    else:
        issues.append("INVALID_RECEIVER: Receiver address is missing or invalid")

    print("[ ] Payer != Receiver")
    if payer_address == receiver_address:
        issues.append("SERVER_CONFIGURATION_ERROR: Payer address is exactly the same as Receiver address!")
    elif payer_address and receiver_address:
        print("[X] Payer != Receiver")
        
    # Check Facilitator Config
    facil_url = settings.X402_FACILITATOR_URL
    print(f"[ ] Facilitator URL = {facil_url}")
    if not facil_url:
        issues.append("X402_CONFIGURATION_ERROR: Facilitator URL is not configured")
    else:
        print("[X] Facilitator URL is configured")
        
    print("[ ] Facilitator is reachable")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{facil_url.rstrip('/')}/health", timeout=5.0)
            print("[X] Facilitator is reachable (Note: health endpoint may return 404, but it is reachable)")
    except Exception as e:
        issues.append(f"FACILITATOR_ERROR: Facilitator unreachable: {e}")

    # Check Testnet state via Algonode
    algod_client = algod.AlgodClient("", settings.ALGOD_TESTNET_URL, headers={"User-Agent": "DoIt"})
    
    async def check_account(addr, name):
        print(f"[ ] {name} account exists")
        try:
            acc_info = algod_client.account_info(addr)
            print(f"[X] {name} account exists")
            
            # Check ALGO balance
            algo_bal = acc_info.get('amount', 0)
            print(f"[ ] {name} has sufficient ALGO: {algo_bal / 1_000_000} ALGO")
            if algo_bal < 100000: # Needs at least 0.1 ALGO for opt-in/fees
                issues.append(f"INSUFFICIENT_ALGO: {name} has less than 0.1 ALGO")
            else:
                print(f"[X] {name} has sufficient ALGO")
                
            # Check USDC Opt-In and Balance
            print(f"[ ] {name} is opted into USDC")
            usdc_asset = next((a for a in acc_info.get('assets', []) if str(a['asset-id']) == str(asset_id)), None)
            if not usdc_asset:
                issues.append(f"USDC_OPT_IN_ERROR: {name} is NOT opted into USDC Asset {asset_id}")
            else:
                print(f"[X] {name} is opted into USDC")
                usdc_bal = usdc_asset.get('amount', 0)
                print(f"    {name} USDC Balance: {usdc_bal / 1_000_000} USDC")
                if name == "Payer" and usdc_bal < 50000:
                    issues.append(f"INSUFFICIENT_USDC: {name} has insufficient USDC for payment (Requires at least 0.05 USDC)")
                
        except Exception as e:
            if "not found" in str(e).lower():
                issues.append(f"WALLET_CONFIGURATION_ERROR: {name} account {addr} does not exist on TestNet")
            else:
                issues.append(f"WALLET_CONFIGURATION_ERROR: Error fetching {name} account: {e}")

    if payer_address:
        await check_account(payer_address, "Payer")
    if receiver_address:
        await check_account(receiver_address, "Receiver")

    # Check x402 Server configuration
    from app.services.x402_service import network_str
    print(f"[ ] x402 server configuration uses TestNet")
    if "testnet" in network_str or "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=" in network_str:
        print("[X] x402 server configuration uses TestNet")
    else:
        issues.append("X402_CONFIGURATION_ERROR: x402 server network is not TestNet")
        
    print(f"\n==================================================")
    if issues:
        print("DIAGNOSTIC FAILED WITH THE FOLLOWING ISSUES:")
        for issue in issues:
            print(f" - {issue}")
    else:
        print("DIAGNOSTIC PASSED! Ready for real x402 E2E test.")
        
    return issues

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
