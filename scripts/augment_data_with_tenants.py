#!/usr/bin/env python3
"""
Augment test data with tenant_id columns for multi-tenant isolation.

This script adds tenant_id columns to CLV and Risk data files:
- CLV: All records assigned to Acme tenant
- Risk: 60% Acme, 40% Beta (demonstrates multi-tenant access)
"""
import pandas as pd
from pathlib import Path

ACME_TENANT_ID = "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"
BETA_TENANT_ID = "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"

def augment_clv_data():
    """Add tenant_id to CLV data (Acme only)."""
    clv_file = Path("data/mock-data/clv/data.csv")

    if not clv_file.exists():
        print(f"ERROR: CLV data file not found at {clv_file}")
        return False

    print(f"Reading CLV data from {clv_file}...")
    df = pd.read_csv(clv_file)

    # Add tenant_id column
    df['tenant_id'] = ACME_TENANT_ID

    # Save back to file
    df.to_csv(clv_file, index=False)

    print(f"✓ Augmented CLV data: {len(df)} records assigned to Acme tenant")
    print(f"  Columns: {', '.join(df.columns[-5:])}")  # Show last 5 columns
    return True

def augment_risk_data():
    """Add tenant_id to Risk data (Acme + Beta split)."""
    risk_file = Path("data/mock-data/risk/data.csv")

    if not risk_file.exists():
        print(f"ERROR: Risk data file not found at {risk_file}")
        return False

    print(f"Reading Risk data from {risk_file}...")
    df = pd.read_csv(risk_file)

    # Split data: 60% Acme, 40% Beta
    split_idx = int(len(df) * 0.6)
    df_acme = df.iloc[:split_idx].copy()
    df_beta = df.iloc[split_idx:].copy()

    df_acme['tenant_id'] = ACME_TENANT_ID
    df_beta['tenant_id'] = BETA_TENANT_ID

    # Combine and shuffle
    df_combined = pd.concat([df_acme, df_beta]).sample(frac=1, random_state=42)

    # Save back to file
    df_combined.to_csv(risk_file, index=False)

    print(f"✓ Augmented Risk data:")
    print(f"  Acme: {len(df_acme)} records")
    print(f"  Beta: {len(df_beta)} records")
    print(f"  Total: {len(df_combined)} records (shuffled)")
    print(f"  Columns: {', '.join(df_combined.columns[-5:])}")
    return True

def verify_augmentation():
    """Verify tenant_id columns exist and distribution is correct."""
    print("\n=== Verification ===")

    # Verify CLV
    clv_file = Path("data/mock-data/clv/data.csv")
    if clv_file.exists():
        df_clv = pd.read_csv(clv_file)
        if 'tenant_id' in df_clv.columns:
            tenant_counts = df_clv['tenant_id'].value_counts()
            print(f"CLV tenant distribution:")
            for tenant_id, count in tenant_counts.items():
                tenant_name = "Acme" if tenant_id == ACME_TENANT_ID else "Beta"
                print(f"  {tenant_name}: {count} records")
        else:
            print("ERROR: tenant_id column not found in CLV data")

    # Verify Risk
    risk_file = Path("data/mock-data/risk/data.csv")
    if risk_file.exists():
        df_risk = pd.read_csv(risk_file)
        if 'tenant_id' in df_risk.columns:
            tenant_counts = df_risk['tenant_id'].value_counts()
            print(f"Risk tenant distribution:")
            for tenant_id, count in tenant_counts.items():
                tenant_name = "Acme" if tenant_id == ACME_TENANT_ID else "Beta"
                percentage = (count / len(df_risk)) * 100
                print(f"  {tenant_name}: {count} records ({percentage:.1f}%)")
        else:
            print("ERROR: tenant_id column not found in Risk data")

if __name__ == "__main__":
    print("=== Augmenting Test Data with Tenant IDs ===\n")

    success = True

    # Augment CLV data
    if not augment_clv_data():
        success = False

    print()

    # Augment Risk data
    if not augment_risk_data():
        success = False

    # Verify results
    verify_augmentation()

    if success:
        print("\n✓ Data augmentation completed successfully!")
    else:
        print("\n✗ Data augmentation failed. Check errors above.")
        exit(1)
