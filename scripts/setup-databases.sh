#!/bin/bash

# Database Setup Script for FastAPI Image Processing Service
# This script helps set up PostgreSQL and SQL Server databases

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}Database Setup for FastAPI Service${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

show_menu() {
    echo "Select database to set up:"
    echo "1) PostgreSQL"
    echo "2) SQL Server"
    echo "3) Both"
    echo "4) Exit"
}

setup_postgres() {
    echo -e "${GREEN}Setting up PostgreSQL...${NC}"
    echo ""
    
    # Get connection details
    echo "Enter PostgreSQL connection details:"
    read -p "Host [localhost]: " PG_HOST
    PG_HOST=${PG_HOST:-localhost}
    
    read -p "Port [5432]: " PG_PORT
    PG_PORT=${PG_PORT:-5432}
    
    read -p "Database name [images_db]: " PG_DB
    PG_DB=${PG_DB:-images_db}
    
    read -p "Username: " PG_USER
    
    echo "Password: "
    read -s PG_PASS
    echo ""
    
    # Check if database exists
    echo -e "${YELLOW}Checking if database exists...${NC}"
    export PGPASSWORD=$PG_PASS
    
    if psql -h $PG_HOST -p $PG_PORT -U $PG_USER -lqt | cut -d \| -f 1 | grep -qw $PG_DB; then
        echo -e "${GREEN}Database $PG_DB exists${NC}"
    else
        echo -e "${YELLOW}Database $PG_DB does not exist. Creating...${NC}"
        createdb -h $PG_HOST -p $PG_PORT -U $PG_USER $PG_DB
        echo -e "${GREEN}Database created${NC}"
    fi
    
    # Run the schema
    echo -e "${YELLOW}Creating tables and indexes...${NC}"
    psql -h $PG_HOST -p $PG_PORT -U $PG_USER -d $PG_DB -f sql/postgres_schema.sql
    
    # Verify the table was created
    echo -e "${YELLOW}Verifying table creation...${NC}"
    psql -h $PG_HOST -p $PG_PORT -U $PG_USER -d $PG_DB -c "\dt"
    
    echo -e "${GREEN}✅ PostgreSQL setup complete!${NC}"
    echo ""
    echo "Add these to your .env file:"
    echo "PGHOST=$PG_HOST"
    echo "PGPORT=$PG_PORT"
    echo "PGDATABASE=$PG_DB"
    echo "PGUSER=$PG_USER"
    echo "PGPASSWORD=your-password-here"
    echo ""
}

setup_sqlserver() {
    echo -e "${GREEN}Setting up SQL Server...${NC}"
    echo ""
    
    echo "Enter SQL Server connection details:"
    read -p "Host [localhost]: " SQL_HOST
    SQL_HOST=${SQL_HOST:-localhost}
    
    read -p "Port [1433]: " SQL_PORT
    SQL_PORT=${SQL_PORT:-1433}
    
    read -p "Database name [images_db]: " SQL_DB
    SQL_DB=${SQL_DB:-images_db}
    
    read -p "Username [sa]: " SQL_USER
    SQL_USER=${SQL_USER:-sa}
    
    echo "Password: "
    read -s SQL_PASS
    echo ""
    
    # Check if sqlcmd is available
    if command -v sqlcmd &> /dev/null; then
        echo -e "${YELLOW}Using sqlcmd...${NC}"
        
        # Check if database exists, create if not
        sqlcmd -S $SQL_HOST,$SQL_PORT -U $SQL_USER -P $SQL_PASS -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '$SQL_DB') CREATE DATABASE $SQL_DB"
        
        # Run the schema
        echo -e "${YELLOW}Creating tables and indexes...${NC}"
        sqlcmd -S $SQL_HOST,$SQL_PORT -U $SQL_USER -P $SQL_PASS -d $SQL_DB -i sql/sqlserver_schema.sql
        
        # Verify
        echo -e "${YELLOW}Verifying table creation...${NC}"
        sqlcmd -S $SQL_HOST,$SQL_PORT -U $SQL_USER -P $SQL_PASS -d $SQL_DB -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        
    elif command -v mssql-cli &> /dev/null; then
        echo -e "${YELLOW}Using mssql-cli...${NC}"
        
        # Check if database exists, create if not
        mssql-cli -S $SQL_HOST,$SQL_PORT -U $SQL_USER -P $SQL_PASS -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '$SQL_DB') CREATE DATABASE $SQL_DB"
        
        # Run the schema
        echo -e "${YELLOW}Creating tables and indexes...${NC}"
        mssql-cli -S $SQL_HOST,$SQL_PORT -U $SQL_USER -P $SQL_PASS -d $SQL_DB -i sql/sqlserver_schema.sql
        
    else
        echo -e "${RED}Neither sqlcmd nor mssql-cli found!${NC}"
        echo "Please install one of them:"
        echo "  - sqlcmd: https://docs.microsoft.com/en-us/sql/tools/sqlcmd-utility"
        echo "  - mssql-cli: pip install mssql-cli"
        echo ""
        echo "Or run this SQL manually in SQL Server Management Studio:"
        echo ""
        cat sql/sqlserver_schema.sql
        return 1
    fi
    
    echo -e "${GREEN}✅ SQL Server setup complete!${NC}"
    echo ""
    echo "Add these to your .env file:"
    echo "SQLSERVERHOST=$SQL_HOST"
    echo "SQLSERVERPORT=$SQL_PORT"
    echo "SQLSERVERDB=$SQL_DB"
    echo "SQLSERVERUSER=$SQL_USER"
    echo "SQLSERVERPW=your-password-here"
    echo ""
}

# Main script
cd "$(dirname "$0")/.."  # Go to project root

# Check if SQL files exist
if [ ! -f "sql/postgres_schema.sql" ]; then
    echo -e "${RED}Error: sql/postgres_schema.sql not found!${NC}"
    exit 1
fi

if [ ! -f "sql/sqlserver_schema.sql" ]; then
    echo -e "${RED}Error: sql/sqlserver_schema.sql not found!${NC}"
    exit 1
fi

# Interactive menu
while true; do
    show_menu
    read -p "Enter choice [1-4]: " choice
    
    case $choice in
        1)
            setup_postgres
            ;;
        2)
            setup_sqlserver
            ;;
        3)
            setup_postgres
            setup_sqlserver
            ;;
        4)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done

