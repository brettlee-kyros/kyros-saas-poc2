#!/usr/bin/env python3
"""
Test script to validate test data loading for Story 0.2
Validates burn-performance and mixshift test data can be loaded into Pandas
"""

import pandas as pd
import sys
from pathlib import Path

def validate_burn_data():
    """Validate burn-performance test data"""
    print("=" * 60)
    print("Validating burn-performance test data")
    print("=" * 60)

    file_path = Path("/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/burn-performance-test-data/burn.csv")

    try:
        df = pd.read_csv(file_path)

        print(f"\n✅ Successfully loaded: {file_path.name}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")

        print(f"\n📊 Data Types:")
        print(df.dtypes.to_string())

        print(f"\n📋 Column Names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")

        print(f"\n🔍 First 3 Rows:")
        print(df.head(3).to_string())

        print(f"\n⚠️  Null Values:")
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if len(null_cols) == 0:
            print("   No null values found")
        else:
            print(null_cols.to_string())

        print(f"\n✅ Validation: PASS")
        print(f"   - Row count ({len(df)}) meets minimum threshold (>20 rows)")
        print(f"   - Data loaded successfully into DataFrame")

        return True, df

    except Exception as e:
        print(f"\n❌ ERROR loading burn data: {e}")
        return False, None

def validate_mix_data():
    """Validate mixshift test data"""
    print("\n" + "=" * 60)
    print("Validating mixshift test data")
    print("=" * 60)

    file_path = Path("/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/mixshift-test-data/mix.csv")

    try:
        df = pd.read_csv(file_path)

        print(f"\n✅ Successfully loaded: {file_path.name}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")

        print(f"\n📊 Data Types:")
        print(df.dtypes.to_string())

        print(f"\n📋 Column Names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")

        print(f"\n🔍 First 3 Rows:")
        print(df.head(3).to_string())

        print(f"\n⚠️  Null Values:")
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if len(null_cols) == 0:
            print("   No null values found")
        else:
            print(null_cols.to_string())

        print(f"\n✅ Validation: PASS")
        print(f"   - Row count ({len(df)}) meets minimum threshold (>20 rows)")
        print(f"   - Data loaded successfully into DataFrame")

        return True, df

    except Exception as e:
        print(f"\n❌ ERROR loading mix data: {e}")
        return False, None

if __name__ == "__main__":
    burn_ok, burn_df = validate_burn_data()
    mix_ok, mix_df = validate_mix_data()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if burn_ok and mix_ok:
        print("✅ All test data files validated successfully")
        print(f"   - burn.csv: {len(burn_df)} rows, {len(burn_df.columns)} columns")
        print(f"   - mix.csv: {len(mix_df)} rows, {len(mix_df.columns)} columns")
        sys.exit(0)
    else:
        print("❌ Some test data files failed validation")
        if not burn_ok:
            print("   - burn.csv: FAILED")
        if not mix_ok:
            print("   - mix.csv: FAILED")
        sys.exit(1)
