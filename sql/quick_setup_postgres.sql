-- Quick PostgreSQL Setup for FastAPI Image Processing Service
-- Run this file to quickly set up your PostgreSQL database
--
-- Usage:
--   psql -U your_username -d your_database -f sql/quick_setup_postgres.sql
--
-- Or if creating a new database:
--   createdb -U your_username images_db
--   psql -U your_username -d images_db -f sql/quick_setup_postgres.sql

-- Drop existing table if you want to start fresh (uncomment if needed)
-- DROP TABLE IF EXISTS images CASCADE;

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
    ai_labels JSONB NULL,
    ai_text JSONB NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_images_name ON images(name);
CREATE INDEX IF NOT EXISTS idx_images_date_added ON images(date_added DESC);
CREATE INDEX IF NOT EXISTS idx_images_date_identified ON images(date_identified DESC);
CREATE INDEX IF NOT EXISTS idx_images_ai_labels ON images USING GIN(ai_labels);
CREATE INDEX IF NOT EXISTS idx_images_ai_text ON images USING GIN(ai_text);

-- Insert sample data for testing (optional)
-- INSERT INTO images (name, url, ai_labels) 
-- VALUES ('test.jpg', 'https://example.com/test.jpg', '{"labels": ["test", "sample"]}')
-- ON CONFLICT DO NOTHING;

-- Verify table creation
\dt images

-- Show table structure
\d images

-- Count existing records
SELECT COUNT(*) as total_images FROM images;

-- Success message
SELECT 'PostgreSQL setup complete!' as status;

