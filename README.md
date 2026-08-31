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
1. The backend natively parses `APP_WALLET_PASSPHRASE` on startup. If the derived public key does not match `ALGORAND_RECEIVER_ADDRESS`, the server will safely abort.
2. The frontend uses a custom Axios interceptor and `@x402/core` to build an unsigned Algorand AVM transaction upon hitting a `402`.
3. The frontend utilizes a secure `POST /api/demo/sign-payment` backend endpoint to sign the transaction (keeping the passphrase safely on the server), then settles the payment with GoPlausible to unlock the premium data.

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
- The `demo_wallet` signing endpoint securely signs transactions on behalf of the user for seamless hackathon demonstration. In a true production environment, the frontend would directly utilize a browser-based Algorand wallet extension (e.g., Pera Web) to sign the x402 transaction client-side.
