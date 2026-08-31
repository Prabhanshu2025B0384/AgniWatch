import os
import base64
import nacl.signing
import algosdk
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"
    
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = ""
    DATABASE_URL: str = ""
    
    NASA_FIRMS_MAP_KEY: str = ""
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    
    ALGORAND_NETWORK: str = "testnet"
    ALGOD_TESTNET_URL: str = "https://testnet-api.algonode.cloud"
    ALGOD_TESTNET_TOKEN: str = ""
    
    X402_FACILITATOR_URL: str = "https://facilitator.goplausible.xyz"
    X402_PRICE_USDC: str = "0.05"
    ALGORAND_USDC_ASSET_ID: int = 10458941
    ALGORAND_RECEIVER_ADDRESS: str = ""
    APP_WALLET_PASSPHRASE: str = ""
    APP_WALLET_MNEMONIC: str = "" # Legacy fallback
    
    GEMINI_API_KEY: str = ""
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode='after')
    def validate_wallet(self) -> 'Settings':
        wallet_phrase = self.APP_WALLET_PASSPHRASE or self.APP_WALLET_MNEMONIC
        if wallet_phrase:
            words = wallet_phrase.strip().split()
            if len(words) != 24:
                raise ValueError("Wallet passphrase must be exactly 24 words for Pera Wallet derivation")
            
            try:
                from mnemonic import Mnemonic
                from slip10 import SLIP10
                
                # 1. Get the 512-bit seed from the 24-word phrase
                mnemo = Mnemonic("english")
                seed_bytes = mnemo.to_seed(wallet_phrase)
                
                # 2. Derive the key using SLIP-10 for Ed25519 using the Algorand path m/44'/283'/0'/0'/0'
                node = SLIP10.from_seed(seed_bytes, curve_name='ed25519')
                private_key_seed = node.get_privkey_from_path("m/44'/283'/0'/0'/0'")
                
                signing_key = nacl.signing.SigningKey(private_key_seed)
                verifying_key = signing_key.verify_key
                algo_sk = base64.b64encode(private_key_seed + bytes(verifying_key)).decode('utf-8')
                
                algo_addr = algosdk.account.address_from_private_key(algo_sk)
                
                # Receiver can intentionally be different from the signer account,
                # so we do not raise a ValueError here.
            except Exception as e:
                raise ValueError(f"Failed to validate APP_WALLET_PASSPHRASE: {str(e)}")
            
        return self

settings = Settings()
