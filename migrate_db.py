import sqlite3
import os
from pathlib import Path
import datetime, shutil


def merge_databases():
    main_db_path = 'instance/vidyasaarthi.db'

    downloads_path = Path.home() / "Downloads"
    second_db_path = downloads_path / 'vidyasaarthi.db'

    if not os.path.exists(main_db_path):
        print(f"❌ Error: Cannot find main database at {main_db_path}")
        return
    if not os.path.exists(second_db_path):
        print(f"❌ Error: Cannot find second database at {second_db_path}")
        return

    # Create backup file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = main_db_path.parent / f"vidyasaarthi_backup_{timestamp}.db"

    # Copy database
    shutil.copy2(main_db_path, backup_path)

    print(f"Backup created at: {backup_path}")

    # Connect to both databases
    conn_main = sqlite3.connect(main_db_path)
    conn_main.row_factory = sqlite3.Row
    cursor_main = conn_main.cursor()

    conn_second = sqlite3.connect(second_db_path)
    conn_second.row_factory = sqlite3.Row
    cursor_second = conn_second.cursor()

    # 1. Get all students from Laptop 2
    cursor_second.execute("SELECT * FROM students")
    students_to_merge = cursor_second.fetchall()

    print(f"🔍 Found {len(students_to_merge)} students in Laptop 2. Starting merge...\n")
    success_count = 0
    skip_count = 0

    for student in students_to_merge:
        student_dict = dict(student)
        old_id = student_dict.pop('id')  # Remove old ID to prevent collision

        columns = ', '.join(student_dict.keys())
        placeholders = ', '.join(['?'] * len(student_dict))

        try:
            # 2. Insert Student into Main DB
            cursor_main.execute(f"INSERT INTO students ({columns}) VALUES ({placeholders})",
                                list(student_dict.values()))
            new_student_id = cursor_main.lastrowid  # Get the newly generated safe ID

            # 3. Get all documents for this student from Laptop 2
            cursor_second.execute("SELECT * FROM documents WHERE student_id = ?", (old_id,))
            documents = cursor_second.fetchall()

            for doc in documents:
                doc_dict = dict(doc)
                doc_dict.pop('id')  # Remove old doc ID
                doc_dict['student_id'] = new_student_id  # Link to the new safe Student ID

                doc_cols = ', '.join(doc_dict.keys())
                doc_place = ', '.join(['?'] * len(doc_dict))
                cursor_main.execute(f"INSERT INTO documents ({doc_cols}) VALUES ({doc_place})", list(doc_dict.values()))

            print(f"✅ Successfully Merged: {student_dict['full_name']}")
            success_count += 1

        except sqlite3.IntegrityError as e:
            # This triggers if Aadhaar or Mobile already exists in the main database
            print(
                f"⚠️ Skipped {student_dict['full_name']}: Already exists in main database (Duplicate Aadhaar/Mobile).")
            skip_count += 1

    # Save all changes to the main database
    conn_main.commit()

    conn_main.close()
    conn_second.close()

    print(f"\n🎉 Merge Complete! {success_count} added, {skip_count} skipped.")


if __name__ == "__main__":
    merge_databases()