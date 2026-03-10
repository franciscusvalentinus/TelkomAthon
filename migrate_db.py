#!/usr/bin/env python3
"""
Database Migration Script for AI-Powered Syllabus Generation System

This script initializes the PostgreSQL database schema by executing the SQL
migration file. It creates all necessary tables, indexes, and constraints.

Usage:
    python migrate_db.py

Requirements:
    - PostgreSQL database must be created beforehand
    - Database credentials must be configured in .env file
    - psycopg2-binary package must be installed

The script will:
1. Load database configuration from environment variables
2. Connect to the PostgreSQL database
3. Execute the schema.sql file to create all tables
4. Verify that tables were created successfully
5. Display migration status

Author: AI-Powered Syllabus Generation System
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql, Error

# Load environment variables
load_dotenv()


def get_database_config():
    """
    Load database configuration from environment variables.
    
    Returns:
        dict: Database configuration parameters
        
    Raises:
        ValueError: If required environment variables are missing
    """
    config = {
        'host': os.getenv('DATABASE_HOST', 'localhost'),
        'port': os.getenv('DATABASE_PORT', '5432'),
        'database': os.getenv('DATABASE_NAME', 'syllabus_generator'),
        'user': os.getenv('DATABASE_USER'),
        'password': os.getenv('DATABASE_PASSWORD')
    }
    
    # Validate required fields
    if not config['user']:
        raise ValueError("DATABASE_USER environment variable is required")
    if not config['password']:
        raise ValueError("DATABASE_PASSWORD environment variable is required")
    
    return config


def load_schema_file():
    """
    Load the SQL schema file content.
    
    Returns:
        str: SQL schema content
        
    Raises:
        FileNotFoundError: If schema.sql file is not found
    """
    schema_path = Path(__file__).parent / 'src' / 'database' / 'schema.sql'
    
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found at: {schema_path}\n"
            "Please ensure src/database/schema.sql exists."
        )
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return f.read()


def verify_tables(cursor):
    """
    Verify that all expected tables were created.
    
    Args:
        cursor: Database cursor
        
    Returns:
        list: List of created table names
    """
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    
    return [row[0] for row in cursor.fetchall()]


def run_migration():
    """
    Execute the database migration.
    
    This function:
    1. Loads database configuration
    2. Connects to PostgreSQL
    3. Executes the schema SQL
    4. Verifies table creation
    5. Reports results
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("=" * 70)
    print("AI-Powered Syllabus Generation System - Database Migration")
    print("=" * 70)
    print()
    
    try:
        # Load configuration
        print("📋 Loading database configuration...")
        config = get_database_config()
        print(f"   Host: {config['host']}")
        print(f"   Port: {config['port']}")
        print(f"   Database: {config['database']}")
        print(f"   User: {config['user']}")
        print()
        
        # Load schema file
        print("📄 Loading schema file...")
        schema_sql = load_schema_file()
        print(f"   Schema file loaded successfully ({len(schema_sql)} characters)")
        print()
        
        # Connect to database
        print("🔌 Connecting to database...")
        connection = psycopg2.connect(**config)
        connection.autocommit = True
        cursor = connection.cursor()
        print("   Connected successfully!")
        print()
        
        # Execute migration
        print("🚀 Executing migration...")
        cursor.execute(schema_sql)
        print("   Migration executed successfully!")
        print()
        
        # Verify tables
        print("✅ Verifying table creation...")
        tables = verify_tables(cursor)
        
        expected_tables = [
            'elo_performance_mapping',
            'elos',
            'organization_profiles',
            'performance_tlo_mapping',
            'performances',
            'syllabus_elo_mapping',
            'syllabus_performance_mapping',
            'syllabus_tlo_mapping',
            'syllabi',
            'tlos'
        ]
        
        print(f"   Created {len(tables)} tables:")
        for table in tables:
            status = "✓" if table in expected_tables else "?"
            print(f"   {status} {table}")
        print()
        
        # Check for missing tables
        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print("⚠️  Warning: Some expected tables are missing:")
            for table in missing_tables:
                print(f"   ✗ {table}")
            print()
        
        # Close connection
        cursor.close()
        connection.close()
        
        print("=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Verify database tables: psql -d syllabus_generator -c '\\dt'")
        print("2. Run the application: streamlit run app.py")
        print()
        
        return 0
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print()
        print("Please ensure your .env file contains:")
        print("  - DATABASE_USER")
        print("  - DATABASE_PASSWORD")
        print("  - DATABASE_NAME (optional, defaults to 'syllabus_generator')")
        print("  - DATABASE_HOST (optional, defaults to 'localhost')")
        print("  - DATABASE_PORT (optional, defaults to '5432')")
        print()
        return 1
        
    except FileNotFoundError as e:
        print(f"❌ File Error: {e}")
        print()
        return 1
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database Connection Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Verify database credentials in .env file")
        print("3. Check if database exists: psql -l")
        print("4. Create database if needed: createdb syllabus_generator")
        print()
        return 1
        
    except Error as e:
        print(f"❌ Database Error: {e}")
        print()
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_migration())
