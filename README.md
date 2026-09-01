# AgniWatch 🌍🔥

AgniWatch is an agentic satellite-thermal-intelligence platform built for environmental monitoring, early wildfire detection, and industrial anomaly tracking.

## Architecture & Tech Stack
The platform follows a modular client-server architecture.

### Frontend
- **Framework**: Vite + React (TypeScript)
- **UI/Components**: Material UI (MUI v9)
- **Map Integration**: Leaflet (`react-leaflet`) for displaying global satellite data and custom bounds.
- **Charts**: Recharts

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Database / Auth**: Supabase (PostgreSQL)
- **Payment & Web3**: x402 Payment Protocol, Algorand TestNet (`@x402/core`, `@x402-avm/avm`)
- **Data Integrations**: NASA FIRMS API (Satellite Thermal Data), Overpass API (OpenStreetMap contextual geodata)

### Risk & Classification Engine
> **Note**: The ML risk engine is currently implemented as a **deterministic, rule-based inference engine** (using spatial context and thermal intensity). It does NOT rely on synthetic training data or a mocked `scikit-learn` model. It correlates FRP, brightness, and distance to known forests/industry to generate an explainable risk score.

## Folder Structure
```text
AGNI Watch/
├── backend/                  # FastAPI backend server
│   ├── app/                  # Application code (API routes, services, config)
│   ├── database/             # Supabase schema definitions and SQL migrations
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React frontend client
│   ├── src/                  # Components, services, and routing
│   └── package.json          # Node dependencies
├── .env.example              # Blank environment variables template
├── .gitignore                # Source control ignore rules
├── README.md                 # This file
├── start.bat                 # One-click startup script
└── stop.bat                  # Process teardown script
```

## Local Setup

### 1. Environment Variables
Copy `.env.example` to `.env` in the **root** and/or `backend/.env`. The backend requires the following configuration:

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
NASA_FIRMS_MAP_KEY=...
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
ALGOD_TESTNET_URL=https://testnet-api.algonode.cloud
ALGOD_TESTNET_TOKEN=
X402_FACILITATOR_URL=https://facilitator.goplausible.xyz
ALGORAND_RECEIVER_ADDRESS=...
APP_WALLET_PASSPHRASE="24-word recovery phrase here"
X402_PRICE_USDC=0.05
GEMINI_API_KEY=...
```

### 2. Running Locally (One-Click)
We provide a simple startup script that manages dependency installation, virtual environment creation, and sequential startup.

Simply run:
```cmd
.\start.bat
```
This will:
1. Setup and activate the Python virtual environment.
2. Install all `requirements.txt` dependencies.
3. Start the FastAPI backend on port `8000`.
4. Wait for the backend to become completely healthy and responsive.
5. Install frontend `node_modules`.
6. Start the Vite React app on port `5173` and automatically open your browser.

To safely stop all processes spawned by this project, run:
```cmd
.\stop.bat
```

## Integrations

### Supabase
The backend relies on Supabase for data persistence (caching hotspot analysis and metadata). Ensure your Supabase instance is configured with the schema found in `backend/database/init.sql`.

### Algorand / x402 Web3 Monetization
Deep analysis endpoints (`GET /api/analysis/{hotspot_id}`) are guarded by the HTTP `402 Payment Required` protocol.
1. The backend enforces payment via a FastAPI dependency, utilizing the `authorization` payment flow and expecting a valid `payment-signature` header.
2. The frontend uses a custom Axios interceptor and `@x402/core` to intercept `402` responses.
3. It builds an Algorand AVM transaction and securely settles the payment via the GoPlausible Facilitator (`HTTPFacilitatorClient`).
4. Upon successful settlement, the interceptor automatically retries the original request with the authorized payment signature, unlocking the premium data seamlessly.

### Helper Scripts & Diagnostics
To facilitate x402 local development and testing on the Algorand TestNet, several standalone scripts are provided:
- **Diagnostics**: `backend/diagnostic.py` checks environment variables, wallet ALGO balances, and USDC opt-in statuses.
- **Opt-In Scripts**: `backend/optin_asset.py`, `backend/payer_optin.py`, and `backend/receiver_optin.py` programmatically opt your testnet wallets into the USDC asset.
- **Wait for USDC**: `backend/wait_for_usdc.py` polls your wallet until USDC is received (useful when funding from a faucet).
- **E2E Testing**: `backend/test_e2e_x402.py` and `frontend/test_e2e_x402.ts` perform full end-to-end integration tests of the backend challenge and frontend interceptor payment flow.

### NASA FIRMS & Overpass
Real-time thermal hotspot data is pulled from NASA FIRMS APIs. Contextual geographic data (proximity to industry, forests, and settlements) is pulled via Overpass (OpenStreetMap) to enrich the rule-based risk classification.

## Deployment

### Vercel (Frontend)
The frontend is optimized for deployment on Vercel. 
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variables**: Set `VITE_API_URL` to point to your live Render backend URL.

### Render (Backend)
The backend is optimized for deployment on Render as a Web Service.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: Configure all secrets (Supabase, API Keys, Wallet Passphrase) in the Render dashboard.

## Current Limitations
- ML Engine is rule-based; future phases will introduce genuine historical data training.
- In a true production environment, the frontend would directly utilize a browser-based Algorand wallet extension (e.g., Pera Web, Defly) to sign the x402 transaction client-side, rather than relying on a demo local signer.
