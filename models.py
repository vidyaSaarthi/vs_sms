from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ==========================================
# 1. CORE ENTITIES
# ==========================================

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

    is_approved = db.Column(db.Boolean, default=False)
    exam_type = db.Column(db.String(20), nullable=False)
    forms_filled = db.Column(db.String(500), nullable=True)
    other_forms_filled = db.Column(db.String(250), nullable=True)

    full_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    religion = db.Column(db.String(50), nullable=True)
    identification_mark = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=False)
    aadhaar_no = db.Column(db.String(20), unique=True, nullable=False)
    nationality = db.Column(db.String(50), default='Indian')
    nativity = db.Column(db.String(100), nullable=True)

    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    alt_mobile_number = db.Column(db.String(15), nullable=True)
    emergency_mobile = db.Column(db.String(15), nullable=True)
    email_address = db.Column(db.String(120), nullable=True)
    alt_email = db.Column(db.String(120), nullable=True)
    emergency_email = db.Column(db.String(120), nullable=True)

    house_no = db.Column(db.String(100), nullable=True)
    street_name = db.Column(db.String(150), nullable=True)
    post_office = db.Column(db.String(100), nullable=True)
    pin_code = db.Column(db.String(20), nullable=True)
    state_ut = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)

    father_name = db.Column(db.String(150), nullable=True)
    father_aadhaar_no = db.Column(db.String(20), nullable=True)
    father_education = db.Column(db.String(150), nullable=True)
    father_occupation = db.Column(db.String(150), nullable=True)
    father_designation = db.Column(db.String(150), nullable=True)
    father_organization = db.Column(db.String(150), nullable=True)

    mother_name = db.Column(db.String(150), nullable=True)
    mother_aadhaar_no = db.Column(db.String(20), nullable=True)
    mother_education = db.Column(db.String(150), nullable=True)
    mother_occupation = db.Column(db.String(150), nullable=True)
    mother_designation = db.Column(db.String(150), nullable=True)
    mother_organization = db.Column(db.String(150), nullable=True)

    family_income = db.Column(db.String(100), nullable=True)

    bank_holder_name = db.Column(db.String(150), nullable=True)
    bank_name = db.Column(db.String(150), nullable=True)
    bank_branch = db.Column(db.String(150), nullable=True)
    bank_address = db.Column(db.String(250), nullable=True)
    bank_account_no = db.Column(db.String(50), nullable=True)
    bank_ifsc = db.Column(db.String(20), nullable=True)

    class_10_year = db.Column(db.Integer, nullable=True)
    class_10_school = db.Column(db.String(200), nullable=True)
    class_10_school_type = db.Column(db.String(50), nullable=True)
    class_10_state = db.Column(db.String(100), nullable=True)
    class_10_serial = db.Column(db.String(50), nullable=True)
    class_10_reg_no = db.Column(db.String(50), nullable=True)
    class_10_board = db.Column(db.String(100), nullable=True)
    class_10_issue_date = db.Column(db.Date, nullable=True)
    class_10_roll_no = db.Column(db.String(50), nullable=True)
    class_10_marks_data = db.Column(db.Text, nullable=True)

    class_11_year = db.Column(db.Integer, nullable=True)
    class_11_school = db.Column(db.String(200), nullable=True)
    class_11_state = db.Column(db.String(100), nullable=True)
    class_11_roll_no = db.Column(db.String(50), nullable=True)

    passed_appearing = db.Column(db.String(50), nullable=True)
    studied_sanskrit = db.Column(db.String(20), nullable=True)
    registration_no_apaar_id = db.Column(db.String(100), nullable=True)
    class_12_year = db.Column(db.Integer, nullable=True)
    class_12_school = db.Column(db.String(200), nullable=True)
    class_12_school_type = db.Column(db.String(50), nullable=True)
    class_12_school_code = db.Column(db.String(50), nullable=True)
    class_12_center_code = db.Column(db.String(50), nullable=True)
    class_12_state = db.Column(db.String(100), nullable=True)
    class_12_serial = db.Column(db.String(50), nullable=True)
    class_12_reg_no = db.Column(db.String(50), nullable=True)
    class_12_board = db.Column(db.String(100), nullable=True)
    class_12_issue_date = db.Column(db.Date, nullable=True)
    class_12_roll_no = db.Column(db.String(50), nullable=True)
    class_12_admit_card_id = db.Column(db.String(100), nullable=True)
    class_12_marks_data = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(50))  # FIXED: Comma removed!
    academic_status = db.Column(db.String(50), default='Fresher')

    # Relationships
    documents = db.relationship('Document', backref='student', lazy=True, cascade="all, delete-orphan")
    counselling_registrations = db.relationship('StudentCounsellingRegistration', backref='student', lazy=True)
    round_results = db.relationship('StudentRoundResult', backref='student', lazy=True)


class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    doc_type = db.Column(db.String(100), nullable=False)
    drive_link = db.Column(db.String(500), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==========================================
# 2. MASTER DATA (States, Universities, Exams)
# ==========================================

class State(db.Model):
    __tablename__ = 'states'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    categories = db.relationship('StateCategory', backref='state', lazy=True, cascade="all, delete-orphan")


class StateCategory(db.Model):
    __tablename__ = 'state_categories'
    id = db.Column(db.Integer, primary_key=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    category_description = db.Column(db.Text, nullable=True)


class University(db.Model):
    __tablename__ = 'universities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)

    categories = db.relationship('UniversityCategory', backref='university', lazy=True, cascade="all, delete-orphan")


class UniversityCategory(db.Model):
    __tablename__ = 'university_categories'
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    category_description = db.Column(db.Text, nullable=True)


class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    exam_date = db.Column(db.Date, nullable=True)


# ==========================================
# 3. COUNSELLING & FORMS
# ==========================================

class Counselling(db.Model):
    __tablename__ = 'counselling'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    counselling_type = db.Column(db.String(50), nullable=False)  # 'State' or 'University'

    # Exclusive Foreign Keys based on type
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=True)

    eligibility_criteria = db.Column(db.Text, nullable=True)
    security_fees = db.Column(db.Numeric(10, 2), nullable=True)
    required_documents = db.Column(db.Text, nullable=True)  # JSON or Comma separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    rounds = db.relationship('CounsellingRound', backref='counselling', lazy=True, cascade="all, delete-orphan")


class Form(db.Model):
    __tablename__ = 'forms'
    id = db.Column(db.Integer, primary_key=True)
    form_type = db.Column(db.String(50), nullable=False)  # 'Exam' or 'Counselling'
    name = db.Column(db.String(200), nullable=False)

    # Exclusive Foreign Keys based on type
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=True)
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id'), nullable=True)

    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    admit_card_date = db.Column(db.Date, nullable=True)
    admit_card_link = db.Column(db.String(500), nullable=True)
    document_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==========================================
# 4. ROUNDS & SCHEDULES
# ==========================================

class CounsellingRound(db.Model):
    __tablename__ = 'counselling_rounds'
    id = db.Column(db.Integer, primary_key=True)
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id'), nullable=False)
    round_number = db.Column(db.String(50), nullable=False)  # e.g., "Round 1", "Mop-Up"
    rules = db.Column(db.Text, nullable=True)
    seat_matrix_link = db.Column(db.String(500), nullable=True)
    cutoffs_link = db.Column(db.String(500), nullable=True)
    result_link = db.Column(db.String(500), nullable=True)

    # Relationships
    schedules = db.relationship('RoundSchedule', backref='round', lazy=True, cascade="all, delete-orphan")


class RoundSchedule(db.Model):
    __tablename__ = 'round_schedules'
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('counselling_rounds.id'), nullable=False)
    activity_name = db.Column(db.String(150), nullable=False)  # e.g., "Choice Filling"
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)


# ==========================================
# 5. COLLEGES DIRECTORY
# ==========================================

class College(db.Model):
    __tablename__ = 'colleges'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    college_type = db.Column(db.String(50), nullable=False)  # 'Government', 'Private', 'Deemed', 'Other'
    established_year = db.Column(db.Integer, nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=True)

    fees = db.Column(db.String(200), nullable=True)  # String allows "1.5L/Year"
    service_bond = db.Column(db.Text, nullable=True)
    discontinued_bond = db.Column(db.Text, nullable=True)
    college_information = db.Column(db.Text, nullable=True)
    courses_offered = db.Column(db.Text, nullable=True)
    joining_documents = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==========================================
# 6. STUDENT JOURNEY (Junction Tables)
# ==========================================

class StudentCounsellingRegistration(db.Model):
    __tablename__ = 'student_counselling_registrations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id'), nullable=False)

    application_number = db.Column(db.String(100), nullable=True)
    registration_date = db.Column(db.Date, nullable=True)
    fee_status = db.Column(db.String(50), default='Pending')  # 'Pending', 'Paid'
    documents_verified = db.Column(db.Boolean, default=False)

    # Allows us to do `registration.counselling.name` easily in the UI
    counselling = db.relationship('Counselling', backref='student_registrations', lazy=True)


class StudentRoundResult(db.Model):
    __tablename__ = 'student_round_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('counselling_rounds.id'), nullable=False)

    choices_submitted = db.Column(db.Boolean, default=False)
    allotted_institute = db.Column(db.String(250), nullable=True)
    allotted_branch = db.Column(db.String(150), nullable=True)
    allotted_category = db.Column(db.String(100), nullable=True)

    post_allotment_action = db.Column(db.String(50), nullable=True)  # 'Freeze', 'Float', 'Slide', 'Surrender', etc.
    seat_acceptance_fee_paid = db.Column(db.Boolean, default=False)
    reporting_status = db.Column(db.String(100), default='Not Reported')

    # Allows us to do `result.round.round_number` easily in the UI
    round = db.relationship('CounsellingRound', backref='student_results', lazy=True)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    # Relationship to link back to colleges
    colleges = db.relationship('College', backref='course_ref', lazy=True)

    def __repr__(self):
        return f'<Course {self.name}>'