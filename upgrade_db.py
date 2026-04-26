import sqlite3


def upgrade():
    # Connect to your LIVE database
    conn = sqlite3.connect('instance/vidyasaarthi.db')
    c = conn.cursor()

    # List of all the new columns to inject
    new_columns = [
        ("blood_group", "VARCHAR(10)"),
        ("religion", "VARCHAR(50)"),
        ("class_10_school_type", "VARCHAR(50)"),
        ("class_12_school_type", "VARCHAR(50)"),
        ("class_12_school_code", "VARCHAR(50)"),
        ("class_12_center_code", "VARCHAR(50)"),
        ("class_12_admit_card_id", "VARCHAR(100)"),
        ("father_designation", "VARCHAR(150)"),
        ("mother_designation", "VARCHAR(150)"),
        ("father_organization", "VARCHAR(150)"),
        ("mother_organization", "VARCHAR(150)")
    ]

    for col, dtype in new_columns:
        try:
            c.execute(f"ALTER TABLE students ADD COLUMN {col} {dtype}")
            print(f"✅ Safely Added column: {col}")
        except sqlite3.OperationalError:
            print(f"⚠️ Column {col} already exists. Skipping.")

    conn.commit()
    conn.close()
    print("\n🎉 Database successfully upgraded! Existing data is perfectly safe.")


if __name__ == '__main__':
    upgrade()