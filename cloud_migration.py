import sqlite3
import os
from models import db, Student, Staff, Document
from app import app

# 1. Paste your new Cloud PostgreSQL URL here
CLOUD_DB_URL = "postgresql://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@postgres.railway.internal:5432/railway"


def push_to_cloud():
    # Connect to local SQLite
    local_conn = sqlite3.connect('instance/vidyasaarthi.db')
    local_conn.row_factory = sqlite3.Row
    local_cursor = local_conn.cursor()

    # Temporarily point Flask app to Cloud DB
    app.config['SQLALCHEMY_DATABASE_URI'] = CLOUD_DB_URL

    with app.app_context():
        print("🌐 Connecting to Cloud Database...")
        db.create_all()  # Ensure cloud tables exist

        # 1. Migrate Staff
        local_cursor.execute("SELECT * FROM staff")
        for row in local_cursor.fetchall():
            if not Staff.query.filter_by(username=row['username']).first():
                new_staff = Staff(**{k: row[k] for k in row.keys() if k != 'id'})
                db.session.add(new_staff)

        # 2. Migrate Students & Documents
        local_cursor.execute("SELECT * FROM students")
        students = local_cursor.fetchall()

        print(f"🚀 Pushing {len(students)} students to the cloud...")
        for s_row in students:
            if not Student.query.filter_by(aadhaar_no=s_row['aadhaar_no']).first():
                student_data = {k: s_row[k] for k in s_row.keys() if k != 'id'}
                new_student = Student(**student_data)
                db.session.add(new_student)
                db.session.flush()  # Get the new cloud ID

                local_cursor.execute("SELECT * FROM documents WHERE student_id = ?", (s_row['id'],))
                docs = local_cursor.fetchall()
                for d_row in docs:
                    doc_data = {k: d_row[k] for k in d_row.keys() if k not in ('id', 'student_id')}
                    doc_data['student_id'] = new_student.id
                    db.session.add(Document(**doc_data))

        db.session.commit()
        print("✅ Cloud Migration Complete! Your live data is now secure in the cloud.")


if __name__ == '__main__':
    push_to_cloud()