from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize the database object
db = SQLAlchemy()


class Staff(db.Model, UserMixin):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='counselor')  # 'admin' or 'counselor'
    is_active = db.Column(db.Boolean, default=True)


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)

    # --- 1. Basic Details ---
    full_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    identification_mark = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), nullable=False)  # General/SC/ST/OBC
    place_of_residence = db.Column(db.String(50), nullable=True)  # Urban/Rural
    aadhaar_no = db.Column(db.String(20), unique=True, nullable=False)

    # Login & Core Contact
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    email_address = db.Column(db.String(120), nullable=True)
    student_password = db.Column(db.String(100), nullable=True)  # For portal logins if needed later

    nationality = db.Column(db.String(50), default='Indian')
    nativity = db.Column(db.String(100), nullable=True)  # e.g., Haryana
    course_selected = db.Column(db.String(100), nullable=True)

    # --- 2. Parent Details ---
    father_name = db.Column(db.String(150), nullable=False)
    father_native_district = db.Column(db.String(100), nullable=True)
    father_education = db.Column(db.String(100), nullable=True)
    father_occupation = db.Column(db.String(150), nullable=True)

    mother_name = db.Column(db.String(150), nullable=False)
    mother_native_district = db.Column(db.String(100), nullable=True)
    mother_education = db.Column(db.String(100), nullable=True)
    mother_occupation = db.Column(db.String(150), nullable=True)

    # --- 3. Communication Details ---
    alt_mobile_number = db.Column(db.String(15), nullable=True)
    alt_email_address = db.Column(db.String(120), nullable=True)

    # Present Address
    present_house_no = db.Column(db.String(50), nullable=True)
    present_street_name = db.Column(db.String(150), nullable=True)
    present_post_office = db.Column(db.String(100), nullable=True)
    present_pin_code = db.Column(db.String(10), nullable=True)
    present_state = db.Column(db.String(50), nullable=True)
    present_district = db.Column(db.String(100), nullable=True)

    # Permanent Address
    permanent_address = db.Column(db.Text, nullable=True)

    # --- 4. Academic Details ---
    class_10_year = db.Column(db.Integer, nullable=True)
    class_11_year = db.Column(db.Integer, nullable=True)
    class_12_year = db.Column(db.Integer, nullable=True)

    qualifying_exam = db.Column(db.String(100), nullable=True)  # e.g., 10+2
    qualifying_exam_status = db.Column(db.String(50), nullable=True)  # Passed/Appearing
    board_of_study = db.Column(db.String(100), nullable=True)  # e.g., CBSE
    registration_no_apaar_id = db.Column(db.String(100), nullable=True)
    studied_sanskrit = db.Column(db.String(20), nullable=True)  # Yes/No
    class_12_school_name = db.Column(db.String(200), nullable=True)
    class_12_roll_no = db.Column(db.String(50), nullable=True)

    # Relationships & Metadata
    documents = db.relationship('Document', backref='student', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)  # The local JPG preview
    drive_link = db.Column(db.String(500), nullable=True)  # NEW: The Google Drive PDF link
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)