import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime


def run_backup():
    db_url = os.environ.get('DATABASE_URL')

    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in environment variables!")
        sys.exit(1)  # This tells GitHub the job FAILED

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
    elif db_url.startswith("postgresql://") and "pg8000" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

    engine = create_engine(db_url)
    tables = ['student', 'document', 'counselling', 'counselling_round', 'student_counselling', 'staff']
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"VidyaSaarthi_Backup_{date_str}.xlsx"

    print("Connecting to Railway Cloud...")

    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for table in tables:
                print(f"Exporting {table}...")
                df = pd.read_sql_table(table, engine)
                df.to_excel(writer, sheet_name=table.capitalize(), index=False)

        print(f"✅ Success! Backup saved as {filename}")
    except Exception as e:
        print(f"❌ ERROR: Backup failed: {e}")
        sys.exit(1)  # This tells GitHub the job FAILED


if __name__ == '__main__':
    run_backup()