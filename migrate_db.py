from pathlib import Path
import sqlite3
from datetime import datetime
import shutil


def merge_databases():
    # Define paths
    main_db_path = Path('instance/vidyasaarthi.db')
    downloads_path = Path.home() / "Downloads"
    second_db_path = downloads_path / 'vidyasaarthi.db'

    # Check if files exist
    if not main_db_path.exists():
        print(f"❌ Error: Cannot find main database at {main_db_path}")
        return
    if not second_db_path.exists():
        print(f"❌ Error: Cannot find second database at {second_db_path}")
        return

    # 📁 Backup Main Database
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = main_db_path.parent / f"vidyasaarthi_backup_{timestamp}.db"

    try:
        shutil.copy2(main_db_path, backup_path)
        print(f"📁 Backup created safely at: {backup_path}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return

    # Connect to both databases
    conn_main = sqlite3.connect(main_db_path)
    conn_main.row_factory = sqlite3.Row
    cursor_main = conn_main.cursor()

    conn_second = sqlite3.connect(second_db_path)
    conn_second.row_factory = sqlite3.Row
    cursor_second = conn_second.cursor()

    # Get all students from Laptop 2
    cursor_second.execute("SELECT * FROM students")
    students_to_merge = cursor_second.fetchall()

    print(f"\n🔍 Found {len(students_to_merge)} students in Laptop 2. Starting merge...\n")
    success_count = 0
    overwrite_count = 0

    for student in students_to_merge:
        student_dict = dict(student)
        old_id = student_dict.pop('id')  # Remove old ID to prevent collision

        # ==========================================
        # 🧠 INTELLIGENT MATCHING LOGIC
        # ==========================================

        # PLAN A & B: Look for existing Aadhaar/Mobile OR exact Name+DOB+Father match
        cursor_main.execute("""
            SELECT id FROM students 
            WHERE aadhaar_no = ? 
               OR mobile_number = ? 
               OR (full_name = ? AND dob = ? AND father_name = ? AND full_name != '' AND dob IS NOT NULL)
        """, (
            student_dict.get('aadhaar_no'),
            student_dict.get('mobile_number'),
            student_dict.get('full_name'),
            student_dict.get('dob'),
            student_dict.get('father_name')
        ))

        existing_record = cursor_main.fetchone()

        if existing_record:
            # 🗑️ DELETE & REPLACE LOGIC
            existing_id = existing_record['id']

            # 1. Delete all old documents tied to the old record
            cursor_main.execute("DELETE FROM documents WHERE student_id = ?", (existing_id,))

            # 2. Delete the old student record completely from Main DB
            cursor_main.execute("DELETE FROM students WHERE id = ?", (existing_id,))

            # 3. Insert the fresh student data from Laptop 2 as a brand new row
            columns = ', '.join(student_dict.keys())
            placeholders = ', '.join(['?'] * len(student_dict))
            cursor_main.execute(f"INSERT INTO students ({columns}) VALUES ({placeholders})",
                                list(student_dict.values()))
            new_student_id = cursor_main.lastrowid

            # 4. Attach the fresh documents from Laptop 2 to this new row
            cursor_second.execute("SELECT * FROM documents WHERE student_id = ?", (student['id'],))
            documents = cursor_second.fetchall()

            for doc in documents:
                doc_dict = {key: doc[key] for key in doc.keys() if key != 'id'}
                doc_dict['student_id'] = new_student_id
                doc_cols = ', '.join(doc_dict.keys())
                doc_place = ', '.join(['?'] * len(doc_dict))
                cursor_main.execute(f"INSERT INTO documents ({doc_cols}) VALUES ({doc_place})", list(doc_dict.values()))

            print(f"🗑️ Deleted old record & Inserted fresh copy: {student_dict['full_name']}")
            overwrite_count += 1

        else:
            # ➕ INSERT NEW LOGIC (No match found)
            columns = ', '.join(student_dict.keys())
            placeholders = ', '.join(['?'] * len(student_dict))

            cursor_main.execute(f"INSERT INTO students ({columns}) VALUES ({placeholders})",
                                list(student_dict.values()))
            new_student_id = cursor_main.lastrowid

            # Attach Documents
            cursor_second.execute("SELECT * FROM documents WHERE student_id = ?", (old_id,))
            documents = cursor_second.fetchall()

            for doc in documents:
                doc_dict = dict(doc)
                doc_dict.pop('id')
                doc_dict['student_id'] = new_student_id
                doc_cols = ', '.join(doc_dict.keys())
                doc_place = ', '.join(['?'] * len(doc_dict))
                cursor_main.execute(f"INSERT INTO documents ({doc_cols}) VALUES ({doc_place})", list(doc_dict.values()))

            print(f"✅ Successfully Added New: {student_dict['full_name']}")
            success_count += 1

    # Save all changes to the main database
    conn_main.commit()

    conn_main.close()
    conn_second.close()

    print(f"\n🎉 Merge Complete! {success_count} new students added, {overwrite_count} existing records updated.")


if __name__ == "__main__":
    merge_databases()