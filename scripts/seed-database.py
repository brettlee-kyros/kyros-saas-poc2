#!/usr/bin/env python3
"""
Seed the tenant metadata database with mock data.
Idempotent: Drops and recreates database on each run.
"""
import sqlite3
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "tenant_metadata.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def seed_database():
    """Create and seed the tenant metadata database."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(exist_ok=True)

    # Remove existing database for idempotency
    if DB_PATH.exists():
        print(f"Removing existing database: {DB_PATH}")
        DB_PATH.unlink()

    # Create and seed database
    print(f"Creating database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        # Read and execute schema
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()

        conn.executescript(schema_sql)
        conn.commit()

        # Verify records created
        cursor = conn.cursor()
        tables = ['tenants', 'users', 'user_tenants', 'dashboards', 'tenant_dashboards']

        print("\n✓ Database seeded successfully!")
        print("\nRecord counts:")
        for table in tables:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count}")

        print(f"\nDatabase location: {DB_PATH}")
        print("Run 'python scripts/validate-database.py' to verify.")

    except Exception as e:
        print(f"✗ Error seeding database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()
