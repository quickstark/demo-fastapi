-- Fix PostgreSQL Transaction Error and Set Up Database
-- This script handles the "current transaction is aborted" error

-- First, rollback any failed transaction
ROLLBACK;

-- Now we can proceed with creating the schema
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

-- Commit the changes
COMMIT;

-- Verify table was created
\dt images

-- Show table structure
\d images

-- Test insert to make sure everything works
INSERT INTO images (name, url, ai_labels) 
VALUES ('test_image.jpg', 'https://example.com/test.jpg', '{"labels": ["test"]}')
ON CONFLICT DO NOTHING;

-- Verify the insert worked
SELECT * FROM images WHERE name = 'test_image.jpg';

-- Success message
SELECT 'PostgreSQL setup complete! Table created and tested.' as status;

