import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime


def run_backup():
    # Grab the Database URL from environment variables
    # (We will set this securely in GitHub later)
    db_url = os.environ.get('CLOUD_DB_URL')

    if not db_url:
        print("❌ DATABASE_URL not found!")
        return

    # Ensure it uses the pg8000 driver
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
    elif db_url.startswith("postgresql://") and "pg8000" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

    engine = create_engine(db_url)

    # List every table in your database
    tables = [
        'student', 'document', 'counselling',
        'counselling_round', 'student_counselling', 'staff'
    ]

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"VidyaSaarthi_Backup_{date_str}.xlsx"

    print("Connecting to Railway Cloud...")

    try:
        # Create an Excel writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for table in tables:
                print(f"Exporting {table}...")
                df = pd.read_sql_table(table, engine)
                # Save each table as its own sheet in the Excel file
                df.to_excel(writer, sheet_name=table.capitalize(), index=False)

        print(f"✅ Success! Backup saved as {filename}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")


if __name__ == '__main__':
    run_backup()