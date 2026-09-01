import time
import sys
from app.core.config import settings
from algosdk.v2client import algod
from algosdk.account import address_from_private_key
from mnemonic import Mnemonic
from slip10 import SLIP10
import base64

def main():
    wallet_phrase = settings.APP_WALLET_PASSPHRASE or settings.APP_WALLET_MNEMONIC
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
    
    while True:
        account_info = algod_client.account_info(algo_addr)
        assets = account_info.get('assets', [])
        opted_in = any(a['asset-id'] == asset_id for a in assets)
        if opted_in:
            asset_info = next(a for a in assets if a['asset-id'] == asset_id)
            usdc_balance = asset_info.get('amount', 0) / 1_000_000
            print(f"USDC Balance: {usdc_balance}")
            sys.stdout.flush()
            if usdc_balance > 0:
                print("USDC has arrived!")
                sys.stdout.flush()
                break
        else:
            print("Not opted in yet")
            sys.stdout.flush()
        print("Waiting 5 seconds...")
        sys.stdout.flush()
        time.sleep(5)

if __name__ == "__main__":
    main()
