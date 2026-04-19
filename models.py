from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Staff(db.Model, UserMixin):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='counselor')
    is_active = db.Column(db.Boolean, default=True)


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)

    # 1. Basic Details
    full_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    identification_mark = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    aadhaar_no = db.Column(db.String(20), unique=True, nullable=False)
    nationality = db.Column(db.String(50), default='Indian')
    nativity = db.Column(db.String(100), nullable=True)

    # 2. Communication
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    alt_mobile_number = db.Column(db.String(15), nullable=True)
    emergency_mobile = db.Column(db.String(15), nullable=True)

    email_address = db.Column(db.String(120), nullable=True)
    alt_email = db.Column(db.String(120), nullable=True)
    emergency_email = db.Column(db.String(120), nullable=True)

    # Split Address Fields
    house_no = db.Column(db.String(100), nullable=True)
    street_name = db.Column(db.String(150), nullable=True)
    post_office = db.Column(db.String(100), nullable=True)
    pin_code = db.Column(db.String(20), nullable=True)
    state_ut = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)

    # 3. Parent Details & Finances
    father_name = db.Column(db.String(150), nullable=True)
    father_education = db.Column(db.String(150), nullable=True)
    father_occupation = db.Column(db.String(150), nullable=True)
    mother_name = db.Column(db.String(150), nullable=True)
    mother_education = db.Column(db.String(150), nullable=True)
    mother_occupation = db.Column(db.String(150), nullable=True)
    family_income = db.Column(db.String(100), nullable=True)

    # 4. Bank Details
    bank_holder_name = db.Column(db.String(150), nullable=True)
    bank_name = db.Column(db.String(150), nullable=True)
    bank_branch = db.Column(db.String(150), nullable=True)
    bank_address = db.Column(db.String(250), nullable=True)
    bank_account_no = db.Column(db.String(50), nullable=True)
    bank_ifsc = db.Column(db.String(20), nullable=True)

    # 5. Class 10
    class_10_year = db.Column(db.Integer, nullable=True)
    class_10_school = db.Column(db.String(200), nullable=True)
    class_10_serial = db.Column(db.String(50), nullable=True)
    class_10_reg_no = db.Column(db.String(50), nullable=True)
    class_10_board = db.Column(db.String(100), nullable=True)
    class_10_issue_date = db.Column(db.Date, nullable=True)
    class_10_roll_no = db.Column(db.String(50), nullable=True)
    class_10_marks_data = db.Column(db.Text, nullable=True)

    # 6. Class 11
    class_11_year = db.Column(db.Integer, nullable=True)
    class_11_school = db.Column(db.String(200), nullable=True)
    class_11_roll_no = db.Column(db.String(50), nullable=True)

    # 7. Class 12
    passed_appearing = db.Column(db.String(50), nullable=True)
    studied_sanskrit = db.Column(db.String(20), nullable=True)
    registration_no_apaar_id = db.Column(db.String(100), nullable=True)
    class_12_year = db.Column(db.Integer, nullable=True)
    class_12_school = db.Column(db.String(200), nullable=True)
    class_12_serial = db.Column(db.String(50), nullable=True)
    class_12_reg_no = db.Column(db.String(50), nullable=True)
    class_12_board = db.Column(db.String(100), nullable=True)
    class_12_issue_date = db.Column(db.Date, nullable=True)
    class_12_roll_no = db.Column(db.String(50), nullable=True)
    class_12_marks_data = db.Column(db.Text, nullable=True)

    documents = db.relationship('Document', backref='student', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)
    drive_link = db.Column(db.String(500), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)