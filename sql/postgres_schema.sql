-- PostgreSQL Schema for Images API
-- This schema creates the necessary tables and indexes for the FastAPI application

-- Create the images table
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    width INTEGER NULL,
    height INTEGER NULL,
    url VARCHAR(500) NULL,
    url_resize VARCHAR(500) NULL,
    date_added DATE DEFAULT CURRENT_DATE,
    date_identified DATE NULL,
    ai_labels JSONB NULL,  -- Using JSONB for better performance and indexing
    ai_text JSONB NULL     -- Using JSONB for better performance and indexing
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_images_name ON images(name);
CREATE INDEX IF NOT EXISTS idx_images_date_added ON images(date_added DESC);
CREATE INDEX IF NOT EXISTS idx_images_date_identified ON images(date_identified DESC);

-- Create GIN indexes for JSONB columns (allows efficient JSON queries)
CREATE INDEX IF NOT EXISTS idx_images_ai_labels ON images USING GIN(ai_labels);
CREATE INDEX IF NOT EXISTS idx_images_ai_text ON images USING GIN(ai_text);

-- Optional: Add a text search index for searching within JSON data
-- CREATE INDEX IF NOT EXISTS idx_images_search ON images USING GIN(to_tsvector('english', name || ' ' || COALESCE(ai_labels::text, '') || ' ' || COALESCE(ai_text::text, '')));

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON TABLE images TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE images_id_seq TO your_app_user;
