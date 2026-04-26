import sqlite3
import os
from models import db, Student, Staff, Document
from app import app

# 1. Paste your new Cloud PostgreSQL URL here
# CLOUD_DB_URL = "postgresql+pg8000://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@shuttle.proxy.rlwy.net:59162/railway"
import sqlite3
from models import db, Student, Staff, Document
from app import app
from sqlalchemy import create_engine, text

# 1. Use DATABASE_PUBLIC_URL from Postgres Variables tab
# MUST start with postgresql+pg8000://
# CLOUD_DB_URL = "postgresql+pg8000://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@viaduct.proxy.rlwy.net:59162/railway"
import sqlite3
from datetime import datetime
from models import db, Student, Staff, Document
from app import app
from sqlalchemy import text

# 1. Use DATABASE_PUBLIC_URL from Postgres Variables tab
# MUST start with postgresql+pg8000://
# CLOUD_DB_URL = "postgresql+pg8000://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@shuttle.proxy.rlwy.net:59162/railway"

import sqlite3
from datetime import datetime
from models import db, Student, Staff, Document
from app import app
from sqlalchemy import text

# USE YOUR DATABASE_PUBLIC_URL (with +pg8000)
CLOUD_DB_URL = "postgresql+pg8000://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@shuttle.proxy.rlwy.net:59162/railway"

def parse_date(date_str):
    if not date_str: return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def migrate():
    local_conn = sqlite3.connect('instance/vidyasaarthi.db')
    local_conn.row_factory = sqlite3.Row
    local_cursor = local_conn.cursor()
    local_cursor.execute("SELECT * FROM students")
    local_students = local_cursor.fetchall()

    app.config['SQLALCHEMY_DATABASE_URI'] = CLOUD_DB_URL

    with app.app_context():
        print("🌐 Connecting to Cloud...")
        db.create_all()  # Ensure tables exist one last time

        # 🧨 Clear only students and docs (keep staff to avoid login issues)
        Document.query.delete()
        Student.query.delete()

        print(f"🚀 Pushing {len(local_students)} students...")
        for s_row in local_students:
            s_data = {k: s_row[k] for k in s_row.keys() if k != 'id'}
            s_data['dob'] = parse_date(s_data.get('dob'))
            s_data['class_10_issue_date'] = parse_date(s_data.get('class_10_issue_date'))
            s_data['class_12_issue_date'] = parse_date(s_data.get('class_12_issue_date'))

            new_student = Student(**s_data)
            db.session.add(new_student)
            db.session.flush()

            local_cursor.execute("SELECT * FROM documents WHERE student_id = ?", (s_row['id'],))
            for d_row in local_cursor.fetchall():
                d_data = {k: d_row[k] for k in d_row.keys() if k not in ('id', 'student_id')}
                d_data['student_id'] = new_student.id
                db.session.add(Document(**d_data))

        db.session.commit()
        print("🎉 SUCCESS! 18 Students are live.")


if __name__ == '__main__':
    migrate()