#!/usr/bin/env python3
"""
Validate the tenant metadata database structure and seed data.
"""
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "tenant_metadata.db"


def validate_database():
    """Validate database structure and seed data."""
    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        print("  Run: python scripts/seed-database.py")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    checks_passed = True

    try:
        print("Validating tenant metadata database...\n")

        # Check tenants
        tenants = cursor.execute("SELECT name, slug FROM tenants ORDER BY name").fetchall()
        if len(tenants) != 2:
            print(f"✗ Expected 2 tenants, found {len(tenants)}")
            checks_passed = False
        else:
            print(f"✓ Tenants: {', '.join([t[0] for t in tenants])}")

        # Check users
        users = cursor.execute("SELECT email FROM users ORDER BY email").fetchall()
        if len(users) != 3:
            print(f"✗ Expected 3 users, found {len(users)}")
            checks_passed = False
        else:
            print(f"✓ Users: {', '.join([u[0] for u in users])}")

        # Check user_tenants mappings
        mappings = cursor.execute("SELECT COUNT(*) FROM user_tenants").fetchone()[0]
        if mappings != 4:
            print(f"✗ Expected 4 user_tenants mappings, found {mappings}")
            checks_passed = False
        else:
            print(f"✓ User-tenant mappings: {mappings}")

        # Check dashboards
        dashboards = cursor.execute("SELECT slug, title FROM dashboards ORDER BY slug").fetchall()
        if len(dashboards) != 2:
            print(f"✗ Expected 2 dashboards, found {len(dashboards)}")
            checks_passed = False
        else:
            print(f"✓ Dashboards: {', '.join([d[0] for d in dashboards])}")

        # Check tenant_dashboards
        td = cursor.execute("SELECT COUNT(*) FROM tenant_dashboards").fetchone()[0]
        if td != 3:
            print(f"✗ Expected 3 tenant_dashboards, found {td}")
            checks_passed = False
        else:
            print(f"✓ Tenant-dashboard assignments: {td}")

    except Exception as e:
        print(f"✗ Error validating database: {e}")
        checks_passed = False
    finally:
        conn.close()

    if checks_passed:
        print("\n✓ Database validation passed!")
        return True
    else:
        print("\n✗ Database validation failed!")
        return False


if __name__ == "__main__":
    success = validate_database()
    sys.exit(0 if success else 1)
