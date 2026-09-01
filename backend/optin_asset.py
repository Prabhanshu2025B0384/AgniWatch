import json
import base64
import time
from app.core.config import settings
from algosdk.v2client import algod
from algosdk import transaction
from algosdk.account import address_from_private_key
from mnemonic import Mnemonic
from slip10 import SLIP10

def main():
    wallet_phrase = settings.APP_WALLET_PASSPHRASE or settings.APP_WALLET_MNEMONIC
    if not wallet_phrase:
        print("FAIL: No wallet phrase")
        return
        
    mnemo = Mnemonic("english")
    seed_bytes = mnemo.to_seed(wallet_phrase)
    node = SLIP10.from_seed(seed_bytes, curve_name='ed25519')
    private_key_seed = node.get_privkey_from_path("m/44'/283'/0'/0'/0'")
    
    import nacl.signing
    signing_key = nacl.signing.SigningKey(private_key_seed)
    verifying_key = signing_key.verify_key
    algo_sk = base64.b64encode(private_key_seed + bytes(verifying_key)).decode('utf-8')
    algo_addr = address_from_private_key(algo_sk)
    
    algod_client = algod.AlgodClient("", settings.ALGOD_TESTNET_URL)
    
    asset_id = settings.ALGORAND_USDC_ASSET_ID
    
    account_info = algod_client.account_info(algo_addr)
    algo_balance = account_info.get('amount', 0) / 1_000_000
    
    assets = account_info.get('assets', [])
    opted_in = any(a['asset-id'] == asset_id for a in assets)
    
    usdc_balance = 0
    txid = "N/A"
    confirmed = "N/A"
    
    if opted_in:
        asset_info = next(a for a in assets if a['asset-id'] == asset_id)
        usdc_balance = asset_info.get('amount', 0) / 1_000_000
        txid = "ALREADY_OPTED_IN"
        confirmed = "PASS"
    else:
        params = algod_client.suggested_params()
        txn = transaction.AssetTransferTxn(
            sender=algo_addr,
            sp=params,
            receiver=algo_addr,
            amt=0,
            index=asset_id
        )
        signed_txn = txn.sign(algo_sk)
        txid = algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        tx_info = transaction.wait_for_confirmation(algod_client, txid, 4)
        if tx_info:
            confirmed = "PASS"
        else:
            confirmed = "FAIL"
            
        # Re-fetch balances
        account_info = algod_client.account_info(algo_addr)
        assets = account_info.get('assets', [])
        opted_in = any(a['asset-id'] == asset_id for a in assets)
        if opted_in:
            asset_info = next(a for a in assets if a['asset-id'] == asset_id)
            usdc_balance = asset_info.get('amount', 0) / 1_000_000
            
    print(f"Address: {algo_addr}")
    print(f"ALGO Balance: {algo_balance}")
    print(f"USDC Opt-In: {opted_in}")
    print(f"USDC Balance: {usdc_balance}")
    print(f"TxID: {txid}")
    print(f"Confirmed: {confirmed}")

if __name__ == "__main__":
    main()
