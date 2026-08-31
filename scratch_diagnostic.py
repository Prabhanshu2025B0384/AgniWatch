import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

def check():
    env_path_1 = os.path.join(os.getcwd(), 'backend', '.env')
    env_path_2 = os.path.join(os.getcwd(), '.env')
    
    print("backend/.env EXISTS:", os.path.exists(env_path_1))
    print("root/.env EXISTS:", os.path.exists(env_path_2))
    
    # Read backend/.env to see what keys are there
    if os.path.exists(env_path_1):
        with open(env_path_1, 'r') as f:
            keys = [line.split('=')[0].strip() for line in f if '=' in line]
            print("backend/.env KEYS:", keys)
            print("APP_WALLET_PASSPHRASE in backend/.env:", 'APP_WALLET_PASSPHRASE' in keys)
            print("ALGORAND_RECEIVER_ADDRESS in backend/.env:", 'ALGORAND_RECEIVER_ADDRESS' in keys)

check()
