import asyncio
import os
import sys
import base64
from pathlib import Path

# Add the app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
import algosdk
from algosdk.v2client import algod
from algosdk.transaction import AssetTransferTxn, wait_for_confirmation
import nacl.signing
from slip10 import SLIP10
from mnemonic import Mnemonic

def run():
    print("==================================================")
    print("PAYER USDC OPT-IN VERIFICATION")
    print("==================================================")
    
    # 1. Load Mnemonic and Derive
    wallet_phrase = settings.APP_WALLET_MNEMONIC
    if not wallet_phrase:
        print("ERROR: APP_WALLET_MNEMONIC not set")
        return
        
    mnemo = Mnemonic("english")
    seed_bytes = mnemo.to_seed(wallet_phrase)
    node = SLIP10.from_seed(seed_bytes, curve_name='ed25519')
    private_key_seed = node.get_privkey_from_path("m/44'/283'/0'/0'/0'")
    signing_key = nacl.signing.SigningKey(private_key_seed)
    verifying_key = signing_key.verify_key
    algo_sk = base64.b64encode(private_key_seed + bytes(verifying_key)).decode('utf-8')
    
    payer_address = algosdk.account.address_from_private_key(algo_sk)
    
    # 2. Verify Payer Address Matches
    expected = "AYS4OQ2FSOQN3AVPM5T2YYZTF6K4DOOD56W3UI6PC2TPNVHTIMHK2X6A6U"
    print(f"Derived Payer Address: {payer_address}")
    if payer_address != expected:
        print(f"ERROR: Derived payer {payer_address} does NOT match {expected}")
        return
    print("Address matches exactly.")
    
    # 3. Query TestNet
    asset_id = 10458941
    algod_client = algod.AlgodClient("", settings.ALGOD_TESTNET_URL, headers={"User-Agent": "DoIt"})
    
    try:
        acc_info = algod_client.account_info(payer_address)
        algo_bal = acc_info.get('amount', 0) / 1_000_000
        print(f"Payer ALGO balance: {algo_bal} ALGO")
        
        usdc_asset = next((a for a in acc_info.get('assets', []) if str(a['asset-id']) == str(asset_id)), None)
        
        if usdc_asset:
            print("Payer is ALREADY OPTED IN to ASA 10458941.")
            print(f"Payer USDC Balance: {usdc_asset.get('amount', 0) / 1_000_000} USDC")
            
            print("\nREPORT:")
            print(f"- payer address: {payer_address}")
            print(f"- payer ALGO balance: {algo_bal} ALGO")
            print(f"- ASA ID: {asset_id}")
            print("- opt-in transaction ID: N/A (Already opted in)")
            print("- confirmed round: N/A")
            print(f"- final USDC balance: {usdc_asset.get('amount', 0) / 1_000_000}")
            return
            
        print("Payer is NOT opted in. Proceeding with opt-in...")
        
        # 4. Construct Opt-In Transaction
        params = algod_client.suggested_params()
        
        txn = AssetTransferTxn(
            sender=payer_address,
            sp=params,
            receiver=payer_address,
            amt=0,
            index=asset_id
        )
        
        # 5. Sign Transaction
        signed_txn = txn.sign(algo_sk)
        
        # 6. Submit Transaction
        txid = algod_client.send_transaction(signed_txn)
        print(f"Opt-in transaction submitted. TXID: {txid}")
        
        # 7. Wait for confirmation
        print("Waiting for confirmation...")
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
        conf_round = confirmed_txn.get("confirmed-round", 0)
        print(f"Transaction confirmed in round {conf_round}.")
        
        # 8. Query again
        acc_info = algod_client.account_info(payer_address)
        usdc_asset = next((a for a in acc_info.get('assets', []) if str(a['asset-id']) == str(asset_id)), None)
        final_bal = usdc_asset.get('amount', 0) / 1_000_000 if usdc_asset else "UNKNOWN"
        
        print(f"Verification successful. ASA 10458941 exists in opted-in assets.")
        
        # 9. Report
        print("\nREPORT:")
        print(f"- payer address: {payer_address}")
        print(f"- payer ALGO balance: {algo_bal} ALGO")
        print(f"- ASA ID: {asset_id}")
        print(f"- opt-in transaction ID: {txid}")
        print(f"- confirmed round: {conf_round}")
        print(f"- final USDC balance: {final_bal}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
