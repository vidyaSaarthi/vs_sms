import os
import sys
import pandas as pd
from sqlalchemy import create_engine


def run_restore():
    # 1. Grab your local Environment Variable
    db_url = os.environ.get('CLOUD_DB_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found!")
        sys.exit(1)

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)

    # 2. Specify the exact backup file you downloaded from GitHub
    backup_file = "VidyaSaarthi_Backup_2026-04-27.xlsx"  # Change this to your downloaded file

    if not os.path.exists(backup_file):
        print(f"❌ ERROR: Could not find {backup_file}")
        sys.exit(1)

    print("Connecting to Railway Cloud...")
    engine = create_engine(db_url)

    # 🧠 CRITICAL: The exact order matters for Foreign Keys!
    # Parents must exist before children. Staff > Students > Documents.
    restore_order = ['staff_new', 'students_new', 'documents_new']

    print(f"Reading {backup_file}...")

    try:
        # Load the entire Excel file into memory (dictionary of DataFrames)
        excel_data = pd.read_excel(backup_file, sheet_name=None)

        for table_name in restore_order:
            # Reconstruct how the sheet was named (Capitalized)
            sheet_name = table_name.capitalize()[:31]

            if sheet_name in excel_data:
                df = excel_data[sheet_name]
                print(f"Restoring {len(df)} rows into '{table_name}' table...")

                # Push data back to Postgres
                # if_exists='append' ensures we add to the schema Flask just built
                df.to_sql(table_name, engine, if_exists='append', index=False)
            else:
                print(f"⚠️ Warning: Sheet '{sheet_name}' not found in backup.")

        print("✅ SUCCESS! System Restored.")

    except Exception as e:
        print(f"❌ ERROR: Restore failed: {e}")


if __name__ == '__main__':
    run_restore()