# How to Run SQL Server Setup Commands

## Connection Details
- **Server**: 192.168.1.200:9002
- **Username**: sa
- **Password**: Vall123@
- **Database**: images (will be created)

---

## Method 1: Using Docker Exec (Recommended)

SSH to your GMKTec server and run:

```bash
# Create the database
docker exec sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost \
  -U sa \
  -P 'Vall123@' \
  -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'images') CREATE DATABASE images"

# Verify database was created
docker exec sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost \
  -U sa \
  -P 'Vall123@' \
  -Q "SELECT name, database_id, create_date FROM sys.databases WHERE name = 'images'"
```

---

## Method 2: Run Complete SQL Script

```bash
# SSH to GMKTec and run the full SQL script
docker exec -i sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost \
  -U sa \
  -P 'Vall123@' \
  < /path/to/create_images_database.sql
```

---

## Method 3: Interactive SQL Session

```bash
# Start an interactive sqlcmd session
docker exec -it sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost \
  -U sa \
  -P 'Vall123@'
```

Then run these commands one by one:

```sql
-- 1. Create database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'images')
CREATE DATABASE images;
GO

-- 2. Switch to images database
USE images;
GO

-- 3. Create images table
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
GO

-- 4. Create indexes
CREATE INDEX IX_images_name ON images(name);
CREATE INDEX IX_images_date_added ON images(date_added DESC);
CREATE INDEX IX_images_date_identified ON images(date_identified DESC);
GO

-- 5. Verify setup
SELECT name FROM sys.databases WHERE name = 'images';
SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'images';
GO

-- Type 'exit' to quit sqlcmd
```

---

## Method 4: Using Azure Data Studio or SQL Server Management Studio

1. Connect to: `192.168.1.200,9002`
2. Username: `sa`
3. Password: `Vall123@`
4. Open the file: `sql/create_images_database.sql`
5. Execute the script

---

## Quick Verification Commands

After creating the database, verify everything is set up:

```bash
# List all databases
docker exec sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'Vall123@' \
  -Q "SELECT name FROM sys.databases"

# Check images database exists
docker exec sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'Vall123@' \
  -d images \
  -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"

# Check table structure
docker exec sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'Vall123@' \
  -d images \
  -Q "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'images'"
```

---

## After Database Creation

1. **Update GitHub Secret** (if not already done):
   - Go to GitHub repository settings
   - Update `SQLSERVERPW` to `Vall123@`

2. **Restart FastAPI container**:
   ```bash
   docker restart images-api
   ```

3. **Test the connection**:
   ```bash
   curl http://192.168.1.200:9000/test-sqlserver
   ```

4. **Upload a test image**:
   ```bash
   curl -X POST "http://192.168.1.200:9000/add_image?backend=sqlserver" \
     -F "file=@test-image.jpg"
   ```

---

## Troubleshooting

### If you get "Login failed for user 'sa'"
- Verify the password is correct: `Vall123@`
- Check SQL Server is running: `docker ps | grep sqlserver2019`
- Check container logs: `docker logs sqlserver2019`

### If database creation fails
- Ensure you have sufficient permissions
- Check disk space: `df -h`
- Verify SQL Server is healthy: `docker exec sqlserver2019 /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'Vall123@' -Q "SELECT @@VERSION"`

