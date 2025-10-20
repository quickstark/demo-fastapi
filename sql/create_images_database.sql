-- ============================================================
-- Create 'images' Database in SQL Server
-- ============================================================
-- Run this script on your SQL Server instance at 192.168.1.200:9002
-- Username: sa
-- Password: Vall123@

-- Create the database if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'images')
BEGIN
    CREATE DATABASE images;
    PRINT 'Database "images" created successfully.';
END
ELSE
BEGIN
    PRINT 'Database "images" already exists.';
END
GO

-- Switch to the images database
USE images;
GO

-- Create the images table with schema matching PostgreSQL
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'images')
BEGIN
    CREATE TABLE images (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        width INT NULL,
        height INT NULL,
        url NVARCHAR(500) NULL,
        url_resize NVARCHAR(500) NULL,
        date_added DATE NULL DEFAULT GETDATE(),
        date_identified DATE NULL,
        ai_labels NVARCHAR(MAX) NULL,
        ai_text NVARCHAR(MAX) NULL
    );
    
    -- Create indexes for better query performance
    CREATE INDEX IX_images_name ON images(name);
    CREATE INDEX IX_images_date_added ON images(date_added DESC);
    CREATE INDEX IX_images_date_identified ON images(date_identified DESC);
    
    PRINT 'Table "images" and indexes created successfully.';
END
ELSE
BEGIN
    PRINT 'Table "images" already exists.';
END
GO

-- Verify the database and table were created
SELECT 
    DB_NAME() AS CurrentDatabase,
    COUNT(*) AS TableCount
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'images';
GO

-- Show the table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'images'
ORDER BY ORDINAL_POSITION;
GO

PRINT 'Setup complete! Database and table are ready for use.';

