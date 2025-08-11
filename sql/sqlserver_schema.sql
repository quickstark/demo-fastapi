-- SQL Server Schema for Images API
-- This schema matches the PostgreSQL structure for compatibility

-- Create the images table with proper data types for SQL Server
CREATE TABLE images (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    width INT NULL,
    height INT NULL,
    url NVARCHAR(500) NULL,
    url_resize NVARCHAR(500) NULL,
    date_added DATE NULL DEFAULT GETDATE(),
    date_identified DATE NULL,
    ai_labels NVARCHAR(MAX) NULL,  -- JSON data stored as text
    ai_text NVARCHAR(MAX) NULL     -- JSON data stored as text
);

-- Create indexes for better performance
CREATE INDEX IX_images_name ON images(name);
CREATE INDEX IX_images_date_added ON images(date_added DESC);
CREATE INDEX IX_images_date_identified ON images(date_identified DESC);

-- Add check constraints for JSON data if needed (SQL Server 2016+)
-- Uncomment these if your SQL Server version supports JSON validation
-- ALTER TABLE images ADD CONSTRAINT CK_ai_labels_json CHECK (ISJSON(ai_labels) = 1);
-- ALTER TABLE images ADD CONSTRAINT CK_ai_text_json CHECK (ISJSON(ai_text) = 1);