import os
import sys
import pandas as pd
from sqlalchemy import create_engine, inspect
from datetime import datetime


def run_backup():
    db_url = os.environ.get('DATABASE_URL')

    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in environment variables!")
        sys.exit(1)

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
    elif db_url.startswith("postgresql://") and "pg8000" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

    print("Connecting to Railway Cloud...")
    engine = create_engine(db_url)

    # 🧠 THE FIX: Dynamically fetch exact table names from the database!
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if not tables:
        print("❌ ERROR: No tables found in the database!")
        sys.exit(1)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"VidyaSaarthi_Backup_{date_str}.xlsx"

    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for table in tables:
                print(f"Exporting {table}...")
                df = pd.read_sql_table(table, engine)
                # Cap sheet name at 31 chars (Excel limit)
                safe_sheet_name = table.capitalize()[:31]
                df.to_excel(writer, sheet_name=safe_sheet_name, index=False)

        print(f"✅ Success! Backup saved as {filename}")
    except Exception as e:
        print(f"❌ ERROR: Backup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run_backup()