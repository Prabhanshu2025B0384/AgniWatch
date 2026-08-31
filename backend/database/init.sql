-- Supabase Initial Schema for AgniWatch

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: hotspots
CREATE TABLE IF NOT EXISTS hotspots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    brightness DOUBLE PRECISION,
    frp DOUBLE PRECISION,
    confidence VARCHAR(50),
    acq_date DATE NOT NULL,
    acq_time VARCHAR(10) NOT NULL,
    satellite VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(latitude, longitude, acq_date, acq_time, satellite, source)
);

-- Table: hotspot_geo_context
CREATE TABLE IF NOT EXISTS hotspot_geo_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotspot_id UUID NOT NULL REFERENCES hotspots(id) ON DELETE CASCADE,
    nearest_industry_m DOUBLE PRECISION,
    nearest_forest_m DOUBLE PRECISION,
    nearest_settlement_m DOUBLE PRECISION,
    nearest_road_m DOUBLE PRECISION,
    land_use_tag VARCHAR(100),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(hotspot_id)
);

-- Table: hotspot_analysis
CREATE TABLE IF NOT EXISTS hotspot_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotspot_id UUID NOT NULL REFERENCES hotspots(id) ON DELETE CASCADE,
    classification VARCHAR(50) NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    confidence DOUBLE PRECISION,
    evidence JSONB,
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(hotspot_id)
);

-- Table: agent_requests
CREATE TABLE IF NOT EXISTS agent_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    tools_called JSONB,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Table: payments
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotspot_id UUID REFERENCES hotspots(id) ON DELETE SET NULL,
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10) DEFAULT 'ALGO',
    algorand_tx_id VARCHAR(255),
    facilitator_status VARCHAR(50),
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Row Level Security (RLS) setup (optional but recommended)
ALTER TABLE hotspots ENABLE ROW LEVEL SECURITY;
ALTER TABLE hotspot_geo_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE hotspot_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Allow public read access to free layers (hotspots)
CREATE POLICY "Public read access for hotspots" ON hotspots FOR SELECT USING (true);
-- Hide detailed context from unauthenticated/unpaid
CREATE POLICY "Public read access for basic geo context" ON hotspot_geo_context FOR SELECT USING (true); 
CREATE POLICY "Public read access for basic analysis" ON hotspot_analysis FOR SELECT USING (true);

-- Backend service role will bypass RLS.
