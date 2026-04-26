-- Nexus Agricultural Advisory Database Schema

-- Enable vector extension for pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Farmers table
CREATE TABLE farmers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    aadhaar_number VARCHAR(12),
    bank_account VARCHAR(50),
    bank_ifsc VARCHAR(11),
    mobile_number VARCHAR(20),
    land_area_hectares DECIMAL(10, 2),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    state VARCHAR(100),
    district VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    INDEX idx_user_id (user_id),
    INDEX idx_state_district (state, district),
    INDEX idx_location (latitude, longitude)
);

-- Crop recommendations table
CREATE TABLE crop_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID REFERENCES farmers(id) ON DELETE CASCADE,
    session_id UUID,
    crop_type VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(3, 2),
    season VARCHAR(100),
    suitability_factors JSONB,
    reasoning TEXT,
    weather_data JSONB,
    soil_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
);

-- Schemes table
CREATE TABLE schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    benefits TEXT,
    eligibility_criteria JSONB,
    documents_required JSONB,
    state VARCHAR(100),
    district VARCHAR(100),
    applicable_crops JSONB,
    contact_info JSONB,
    embedding vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_scheme_id (scheme_id),
    INDEX idx_state_category (state, category),
    INDEX idx_applicable_crops USING GIN (applicable_crops),
    INDEX idx_embedding ON schemes USING ivfflat (embedding vector_cosine_ops)
);

-- Interactions/Chat history table
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID REFERENCES farmers(id) ON DELETE SET NULL,
    session_id UUID NOT NULL,
    user_query TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    agent_type VARCHAR(100),
    language VARCHAR(10),
    input_type VARCHAR(50),  -- 'text', 'voice'
    recommended_crop VARCHAR(100),
    matched_schemes JSONB,
    quality_score DECIMAL(3, 2),
    user_feedback VARCHAR(255),
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    INDEX idx_language (language)
);

-- Generated PDFs table
CREATE TABLE generated_pdfs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID REFERENCES farmers(id) ON DELETE CASCADE,
    session_id UUID,
    scheme_id VARCHAR(255),
    file_path VARCHAR(500),
    file_size INTEGER,
    form_data JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX idx_farmer_id (farmer_id),
    INDEX idx_session_id (session_id),
    INDEX idx_expires_at (expires_at)
);

-- Generated audio files table
CREATE TABLE generated_audio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    interaction_id UUID REFERENCES interactions(id) ON DELETE CASCADE,
    audio_type VARCHAR(50),  -- 'transcription', 'synthesis'
    file_path VARCHAR(500),
    file_size INTEGER,
    language VARCHAR(10),
    duration_seconds INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_interaction_id (interaction_id),
    INDEX idx_expires_at (expires_at)
);

-- API audit log table
CREATE TABLE api_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    request_size INTEGER,
    response_size INTEGER,
    processing_time_ms INTEGER,
    user_id VARCHAR(255),
    error_code VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_endpoint_method (endpoint, method),
    INDEX idx_status_code (status_code),
    INDEX idx_created_at (created_at),
    INDEX idx_user_id (user_id)
);

-- Crops master table (for extensibility)
CREATE TABLE crops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    scientific_name VARCHAR(255),
    optimal_temperature_min DECIMAL(5, 2),
    optimal_temperature_max DECIMAL(5, 2),
    optimal_rainfall_min DECIMAL(8, 2),
    optimal_rainfall_max DECIMAL(8, 2),
    season VARCHAR(100),
    growing_period_days INTEGER,
    soil_type_preference JSONB,
    ph_range_min DECIMAL(3, 1),
    ph_range_max DECIMAL(3, 1),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_season (season)
);

-- Insert master crop data
INSERT INTO crops (
    name, scientific_name, optimal_temperature_min, optimal_temperature_max,
    optimal_rainfall_min, optimal_rainfall_max, season, growing_period_days,
    ph_range_min, ph_range_max
) VALUES
('Rice', 'Oryza sativa', 20, 35, 8, 20, 'Kharif', 120, 5.5, 7.0),
('Wheat', 'Triticum aestivum', 12, 25, 2, 8, 'Rabi', 120, 6.0, 7.5),
('Soybean', 'Glycine max', 20, 32, 5, 12, 'Kharif', 100, 6.0, 7.0),
('Groundnut', 'Arachis hypogaea', 25, 35, 3, 8, 'Kharif', 90, 6.0, 7.0),
('Sugarcane', 'Saccharum officinarum', 20, 38, 6, 15, 'Year-round', 360, 6.0, 8.0),
('Cotton', 'Gossypium hirsutum', 20, 40, 2, 8, 'Kharif', 210, 6.5, 8.5),
('Maize', 'Zea mays', 18, 32, 4, 10, 'Kharif', 90, 5.5, 7.5),
('Mustard', 'Brassica juncea', 10, 25, 1, 5, 'Rabi', 90, 6.0, 8.0),
('Chickpea', 'Cicer arietinum', 15, 28, 1, 4, 'Rabi', 100, 6.0, 7.5),
('Lentil', 'Lens culinaris', 12, 25, 1, 4, 'Rabi', 85, 6.0, 8.0),
('Bajra', 'Pennisetum glaucum', 20, 40, 3, 8, 'Kharif', 70, 5.5, 8.0),
('Sorghum', 'Sorghum bicolor', 18, 40, 2, 8, 'Kharif', 110, 5.5, 8.5);

-- Soil types table
CREATE TABLE soil_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    sand_percentage DECIMAL(5, 2),
    silt_percentage DECIMAL(5, 2),
    clay_percentage DECIMAL(5, 2),
    organic_matter_min DECIMAL(3, 1),
    drainage_type VARCHAR(50),
    water_holding_capacity DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- Insert soil types
INSERT INTO soil_types (
    name, description, sand_percentage, silt_percentage, clay_percentage,
    organic_matter_min, drainage_type, water_holding_capacity
) VALUES
('Sandy Loam', 'Light texture, good drainage', 65, 25, 10, 0.5, 'Well-drained', 10),
('Loam', 'Balanced soil, moderate drainage', 40, 40, 20, 1.5, 'Well-drained', 20),
('Clay Loam', 'Medium heavy, moderate drainage', 25, 50, 25, 2.0, 'Moderately-drained', 30),
('Clay', 'Heavy, poor drainage', 10, 30, 60, 2.5, 'Poorly-drained', 40),
('Silty Loam', 'Fine texture, moderate drainage', 25, 65, 10, 1.0, 'Moderately-drained', 25);

-- Create view for farmer interaction summary
CREATE VIEW farmer_interaction_summary AS
SELECT
    f.id,
    f.user_id,
    f.name,
    COUNT(i.id) as total_interactions,
    COUNT(DISTINCT i.agent_type) as unique_agents_used,
    MAX(i.created_at) as last_interaction_at,
    AVG(i.processing_time_ms) as avg_processing_time_ms
FROM farmers f
LEFT JOIN interactions i ON f.id = i.farmer_id
GROUP BY f.id, f.user_id, f.name;

-- Create view for scheme popularity
CREATE VIEW scheme_popularity AS
SELECT
    s.id,
    s.name,
    s.state,
    COUNT(i.id) as recommendation_count,
    AVG(CAST(i.quality_score AS NUMERIC)) as avg_quality_score,
    COUNT(DISTINCT i.farmer_id) as unique_farmers_reached
FROM schemes s
LEFT JOIN interactions i ON i.matched_schemes::jsonb @> jsonb_build_array(jsonb_build_object('id', s.scheme_id))
GROUP BY s.id, s.name, s.state;

-- Create indexes for performance
CREATE INDEX idx_interactions_farmer_created ON interactions(farmer_id, created_at DESC);
CREATE INDEX idx_interactions_session_created ON interactions(session_id, created_at DESC);
CREATE INDEX idx_crop_recommendations_farmer_created ON crop_recommendations(farmer_id, created_at DESC);

-- Create trigger to update farmer updated_at timestamp
CREATE TRIGGER update_farmers_updated_at
BEFORE UPDATE ON farmers
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Functions for common operations
CREATE OR REPLACE FUNCTION get_farmer_profile(p_user_id VARCHAR)
RETURNS TABLE (
    farmer_id UUID,
    name VARCHAR,
    location_state VARCHAR,
    location_district VARCHAR,
    land_area DECIMAL,
    total_interactions INTEGER,
    last_interaction TIMESTAMP
) AS $$
SELECT
    f.id,
    f.name,
    f.state,
    f.district,
    f.land_area_hectares,
    COUNT(i.id)::INTEGER,
    MAX(i.created_at)
FROM farmers f
LEFT JOIN interactions i ON f.id = i.farmer_id
WHERE f.user_id = p_user_id
GROUP BY f.id, f.name, f.state, f.district, f.land_area_hectares;
$$ LANGUAGE SQL;

-- Scheme metadata table (raw ingested data from API Setu / scraping)
CREATE TABLE scheme_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id VARCHAR(255) UNIQUE NOT NULL,
    state VARCHAR(100),
    data JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_scheme_metadata_id (scheme_id),
    INDEX idx_scheme_metadata_state (state)
);

-- Scheme form-filling session tracking
CREATE TABLE scheme_form_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id VARCHAR(255) UNIQUE NOT NULL,
    farmer_id UUID REFERENCES farmers(id) ON DELETE SET NULL,
    scheme_id VARCHAR(255),
    current_step VARCHAR(100) NOT NULL DEFAULT 'pending',
    collected_data JSONB DEFAULT '{}'::jsonb,
    missing_fields JSONB DEFAULT '[]'::jsonb,
    is_eligible BOOLEAN DEFAULT FALSE,
    form_pdf_path VARCHAR(500),
    language VARCHAR(10) DEFAULT 'hi',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_form_session_thread (thread_id),
    INDEX idx_form_session_farmer (farmer_id),
    INDEX idx_form_session_step (current_step)
);

-- Vector similarity search function for schemes with metadata filtering
CREATE OR REPLACE FUNCTION match_schemes(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.72,
    match_count int DEFAULT 5,
    filter_state text DEFAULT '',
    filter_category text DEFAULT 'agriculture'
)
RETURNS TABLE (
    id UUID,
    scheme_id VARCHAR,
    name VARCHAR,
    description TEXT,
    benefits TEXT,
    eligibility_criteria JSONB,
    documents_required JSONB,
    state VARCHAR,
    category VARCHAR,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.scheme_id,
        s.name,
        s.description,
        s.benefits,
        s.eligibility_criteria,
        s.documents_required,
        s.state,
        s.category,
        1 - (s.embedding <=> query_embedding) AS similarity
    FROM schemes s
    WHERE
        (filter_state = '' OR LOWER(s.state) = LOWER(filter_state) OR LOWER(s.state) = 'central')
        AND (filter_category = '' OR LOWER(s.category) = LOWER(filter_category))
        AND s.embedding IS NOT NULL
        AND 1 - (s.embedding <=> query_embedding) > match_threshold
    ORDER BY s.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grants for application user (if using separate DB user)
-- GRANT CONNECT ON DATABASE nexus_db TO nexus_app;
-- GRANT USAGE ON SCHEMA public TO nexus_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nexus_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nexus_app;
