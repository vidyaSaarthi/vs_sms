from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

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

# ==========================================
# 2. MASTER DATA (States, Universities, Exams, Courses)
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


# The Many-to-Many Bridge Table
exam_courses = db.Table('exam_courses',
                        db.Column('exam_id', db.Integer, db.ForeignKey('exams.id'), primary_key=True),
                        db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
                        )

counselling_courses = db.Table('counselling_courses',
    db.Column('counselling_id', db.Integer, db.ForeignKey('counselling.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)

class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    exam_date = db.Column(db.Date, nullable=True)
    exam_end_date = db.Column(db.Date, nullable=True)  # 🚨 NEW: The End Date

    # Relationship to Courses
    courses = db.relationship('Course', secondary=exam_courses, backref=db.backref('exams', lazy=True))


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
    aadhaar_no = db.Column(db.String(20), unique=True, nullable=True)
    nationality = db.Column(db.String(50), default='Indian')
    nativity = db.Column(db.String(100), nullable=True)

    mobile_number = db.Column(db.String(15), unique=True, nullable=True)
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
    created_by = db.Column(db.String(50))
    academic_status = db.Column(db.String(50), default='Fresher')

    # Relationships
    documents = db.relationship('Document', backref='student', lazy=True, cascade="all, delete-orphan")
    counselling_registrations = db.relationship('StudentCounsellingRegistration', backref='student', lazy=True)
    round_results = db.relationship('StudentRoundResult', backref='student', lazy=True)
    exam_results = db.relationship('StudentExamResult', backref='student', lazy=True, cascade="all, delete-orphan")
    form_submissions = db.relationship('StudentFormSubmission', backref='student', lazy=True,
                                       cascade="all, delete-orphan")

    # ... your existing Student columns are above this ...

    @property
    def profile_completion(self):
        # 1. ALL 74 Database Fields (Nothing is left behind)
        core_fields = [
            self.exam_type, self.forms_filled, self.other_forms_filled,
            self.full_name, self.gender, self.dob, self.blood_group, self.religion,
            self.identification_mark, self.category, self.aadhaar_no, self.nationality, self.nativity,
            self.mobile_number, self.alt_mobile_number, self.emergency_mobile,
            self.email_address, self.alt_email, self.emergency_email,
            self.house_no, self.street_name, self.post_office, self.pin_code, self.state_ut, self.district,
            self.father_name, self.father_aadhaar_no, self.father_education, self.father_occupation,
            self.father_designation, self.father_organization,
            self.mother_name, self.mother_aadhaar_no, self.mother_education, self.mother_occupation,
            self.mother_designation, self.mother_organization,
            self.family_income,
            self.bank_holder_name, self.bank_name, self.bank_branch, self.bank_address, self.bank_account_no,
            self.bank_ifsc,
            self.class_10_year, self.class_10_school, self.class_10_school_type, self.class_10_state,
            self.class_10_serial, self.class_10_reg_no, self.class_10_board, self.class_10_issue_date,
            self.class_10_roll_no,
            self.class_11_year, self.class_11_school, self.class_11_state, self.class_11_roll_no,
            self.passed_appearing, self.studied_sanskrit, self.registration_no_apaar_id,
            self.class_12_year, self.class_12_school, self.class_12_school_type, self.class_12_school_code,
            self.class_12_center_code, self.class_12_state, self.class_12_serial, self.class_12_reg_no,
            self.class_12_board, self.class_12_issue_date, self.class_12_roll_no, self.class_12_admit_card_id
        ]

        # 2. ALL 26 Master Document Types
        MASTER_DOC_TYPES = [
            'photo', 'student_signature', 'aadhaar_card', '10th_marksheet', '11th_marksheet', '12th_marksheet',
            'bank_proof', 'birth_certificate', 'residence_proof', 'caste_certificate', 'ews_certificate',
            'family_id', 'character_certificate', 'improvement_marksheet', 'neet_jee_result', 'passport',
            'school_leaving_certificate', 'transfer_certificate', 'father_aadhaar', 'mother_aadhaar',
            'neet_jee_admit_card', 'student_pan_card', 'apaar_id_doc', 'fingerprints', 'driving_license',
            '12th_admit_card'
        ]

        # Count filled core fields
        filled_core = sum(1 for f in core_fields if f is not None and str(f).strip() != '')

        # Count filled documents
        attached_docs = [doc.doc_type for doc in self.documents if doc.drive_link and doc.drive_link.strip() != '']
        filled_docs = sum(1 for doc_type in MASTER_DOC_TYPES if doc_type in attached_docs)

        # Calculate strict percentage (Total exactly 100 points)
        total_fields = len(core_fields) + len(MASTER_DOC_TYPES)
        total_filled = filled_core + filled_docs

        if total_fields == 0: return 0
        return int((total_filled / total_fields) * 100)

    @property
    def completion_color(self):
        score = self.profile_completion
        if score < 50:
            return "danger"
        elif score < 99:
            return "warning"  # Yellow until literally 100%
        else:
            return "success"

class FinanceRecord(db.Model):
    __tablename__ = 'finance_records'  # 🚨 Added this line to link to the old data!
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)

    # 🚨 Update this to be nullable
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)

    # 🚨 ADD THIS NEW LINE: To hold names of students not in the system
    unregistered_name = db.Column(db.String(255), nullable=True)

    service_type = db.Column(db.String(100), nullable=False)
    total_fees = db.Column(db.Float, default=0.0)
    installment_1 = db.Column(db.Float, default=0.0)
    installment_2 = db.Column(db.Float, default=0.0)
    balance_amount = db.Column(db.Float, default=0.0)
    mode_of_payment = db.Column(db.String(50))
    beneficiary_name = db.Column(db.String(100))
    comments = db.Column(db.Text)

    def calculate_balance(self):
        self.balance_amount = self.total_fees - (self.installment_1 + self.installment_2)


class StudentExamResult(db.Model):
    __tablename__ = 'student_exam_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)

    # 🚨 Form & Credential Fields
    application_number = db.Column(db.String(100), nullable=True)
    login_username = db.Column(db.String(100), nullable=True)
    login_password = db.Column(db.String(100), nullable=True)
    registered_email = db.Column(db.String(120), nullable=True)
    registered_mobile = db.Column(db.String(15), nullable=True)
    form_confirmation_link = db.Column(db.String(250), nullable=True)

    # Academic Fields
    score = db.Column(db.Float, nullable=True)
    percentile = db.Column(db.Float, nullable=True)
    all_india_rank = db.Column(db.Integer, nullable=True)
    state_rank = db.Column(db.Integer, nullable=True)

    # 🚨 NEW: The Counselor Comments Field
    comments = db.Column(db.Text, nullable=True)

    exam = db.relationship('Exam')


class StudentActivityStatus(db.Model):
    """
    Tracks whether a specific student has completed a specific actionable activity.
    """
    __tablename__ = 'student_activity_status'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)

    # It can link to EITHER a global activity or a round activity
    global_activity_id = db.Column(db.Integer, db.ForeignKey('counselling_activities.id', ondelete='CASCADE'),
                                   nullable=True)
    round_activity_id = db.Column(db.Integer, db.ForeignKey('round_activities.id', ondelete='CASCADE'), nullable=True)

    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships to pull the activity details easily
    student = db.relationship('Student',
                              backref=db.backref('activity_statuses', lazy=True, cascade="all, delete-orphan"))
    global_activity = db.relationship('CounsellingActivity')
    round_activity = db.relationship('RoundActivity')

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    doc_type = db.Column(db.String(100), nullable=False)
    drive_link = db.Column(db.String(500), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)





# ==========================================
# 3. COUNSELLING & FORMS
# ==========================================

class Counselling(db.Model):
    __tablename__ = 'counselling'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    counselling_type = db.Column(db.String(50), nullable=False)

    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=True)

    # 🚨 course_id HAS BEEN REMOVED FROM HERE!

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=True)

    eligibility_criteria = db.Column(db.Text, nullable=True)
    security_fees = db.Column(db.Numeric(10, 2), nullable=True)
    required_documents = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ==============================
    # RELATIONSHIPS
    # ==============================
    rounds = db.relationship('CounsellingRound', backref='counselling', lazy=True, cascade="all, delete-orphan")
    exam = db.relationship('Exam', backref='counsellings', lazy=True)

    # This bridge handles multiple courses now!
    courses = db.relationship('Course', secondary=counselling_courses, backref=db.backref('counsellings', lazy=True))

    state = db.relationship('State', backref='state_counsellings', lazy=True)
    university = db.relationship('University', backref='uni_counsellings', lazy=True)


class Form(db.Model):
    __tablename__ = 'forms'
    id = db.Column(db.Integer, primary_key=True)
    form_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(200), nullable=False)

    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=True)
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id'), nullable=True)

    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    fee_general = db.Column(db.Numeric(10, 2), nullable=True)
    fee_obc = db.Column(db.Numeric(10, 2), nullable=True)
    fee_sc_st = db.Column(db.Numeric(10, 2), nullable=True)
    fee_female = db.Column(db.Numeric(10, 2), nullable=True)

    admit_card_date = db.Column(db.Date, nullable=True)
    admit_card_link = db.Column(db.String(500), nullable=True)
    document_link = db.Column(db.String(500), nullable=True)
    prospectus_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🚨 NEW RELATIONSHIP: One Form has Many Events
    events = db.relationship('FormEvent', backref='form', lazy=True, cascade="all, delete-orphan")


# 🚨 NEW TABLE
class FormEvent(db.Model):
    __tablename__ = 'form_events'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)

    event_name = db.Column(db.String(150), nullable=False)  # e.g., "Correction Window", "Admit Card Download"
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    event_link = db.Column(db.String(500), nullable=True)  # Link specific to this activity

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🚨 ADD THIS EXACT LINE:
    # form = db.relationship('Form')


# ==========================================
# 4. ROUNDS & SCHEDULES
# ==========================================

class CounsellingRound(db.Model):
    __tablename__ = 'counselling_rounds'
    id = db.Column(db.Integer, primary_key=True)
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id'), nullable=False)

    round_number = db.Column(db.String(50), nullable=False)
    rules = db.Column(db.Text, nullable=True)

    # Note: The hardcoded links and old schedule relationship have been removed!
    # The new RoundActivity and RoundArtifact tables automatically connect here via their backrefs.



# ==========================================
# 5. COURSE & COLLEGES DIRECTORY
# ==========================================

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    colleges = db.relationship('College', backref='course_ref', lazy=True)

    def __repr__(self):
        return f'<Course {self.name}>'


class College(db.Model):
    __tablename__ = 'colleges'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    college_type = db.Column(db.String(50), nullable=False)
    established_year = db.Column(db.Integer, nullable=True)

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=True)

    fees = db.Column(db.String(200), nullable=True)
    service_bond = db.Column(db.Text, nullable=True)
    discontinued_bond = db.Column(db.Text, nullable=True)
    college_information = db.Column(db.Text, nullable=True)
    joining_documents = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    state = db.relationship('State', backref='state_colleges', lazy=True)
    university = db.relationship('University', backref='uni_colleges', lazy=True)

    def __repr__(self):
        return f'<College {self.name}>'


# ==========================================
# 6. STUDENT JOURNEY (Junction Tables)
# ==========================================

class StudentCounsellingRegistration(db.Model):
    __tablename__ = 'student_counselling_registrations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id'), nullable=False)

    application_number = db.Column(db.String(100), nullable=True)
    registration_status = db.Column(db.String(50), default='Planned')

    login_username = db.Column(db.String(150), nullable=True)
    login_password = db.Column(db.String(150), nullable=True)
    registered_email = db.Column(db.String(150), nullable=True)
    registered_mobile = db.Column(db.String(20), nullable=True)
    form_confirmation_link = db.Column(db.String(500), nullable=True)

    registration_date = db.Column(db.Date, nullable=True)
    fee_status = db.Column(db.String(50), default='Pending')
    documents_verified = db.Column(db.Boolean, default=False)

    counselling = db.relationship('Counselling', backref='student_registrations', lazy=True)

    def __repr__(self):
        return f'<Reg {self.application_number}>'


class StudentRoundResult(db.Model):
    __tablename__ = 'student_round_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('counselling_rounds.id'), nullable=False)

    choices_submitted = db.Column(db.Boolean, default=False)
    allotted_institute = db.Column(db.String(250), nullable=True)
    allotted_branch = db.Column(db.String(150), nullable=True)
    allotted_category = db.Column(db.String(100), nullable=True)

    post_allotment_action = db.Column(db.String(50), nullable=True)
    seat_acceptance_fee_paid = db.Column(db.Boolean, default=False)
    reporting_status = db.Column(db.String(100), default='Not Reported')

    offer_letter_link = db.Column(db.String(500), nullable=True)

    round = db.relationship('CounsellingRound', backref='student_results', lazy=True)

    def __repr__(self):
        return f'<Result {self.allotted_institute}>'


# ==========================================
# 7. TASK & WORKFLOW MANAGEMENT
# ==========================================
class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, Completed, Rejected

    assigned_to = db.Column(db.String(50), nullable=False)  # Username of assigned counselor
    assigned_by = db.Column(db.String(50), nullable=False)

    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=True)
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id'), nullable=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to easily pull names in HTML
    exam = db.relationship('Exam')
    counselling = db.relationship('Counselling')
    form = db.relationship('Form')


class StudentFormSubmission(db.Model):
    __tablename__ = 'student_form_submissions'
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)

    # It can belong to either an Exam OR a Counselling process
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id'), nullable=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=True)

    # 🚨 FORGIVING FIELD: True for new forms, NULL for your existing legacy data!
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=True)

    # The migrated credential fields
    application_number = db.Column(db.String(100))
    login_username = db.Column(db.String(150))
    login_password = db.Column(db.String(150))
    registered_email = db.Column(db.String(150))
    registered_mobile = db.Column(db.String(20))
    form_confirmation_link = db.Column(db.String(500))
    submission_date = db.Column(db.Date, default=date.today)

    form = db.relationship('Form', backref='student_submissions')
    # 🚨 NEW: Bridges to get the Umbrella Names for the tracker
    counselling = db.relationship('Counselling', backref='form_submissions')
    exam = db.relationship('Exam', backref='form_submissions')

# ==========================================
# LEVEL 1: THE UMBRELLA & GLOBAL TIMELINE
# ==========================================

class CounsellingActivity(db.Model):
    """
    Global timeline events for the entire counselling process
    (e.g., 'Registration Opens', 'Document Verification Window')
    """
    __tablename__ = 'counselling_activities'

    id = db.Column(db.Integer, primary_key=True)
    # 🚨 FIXED: Points to 'counselling.id' (singular)
    counselling_id = db.Column(db.Integer, db.ForeignKey('counselling.id', ondelete='CASCADE'), nullable=False)

    activity_name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    activity_link = db.Column(db.String(500), nullable=True)

    counselling = db.relationship('Counselling',
                                  backref=db.backref('global_activities', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<CounsellingActivity {self.activity_name}>"


# ==========================================
# LEVEL 2: THE ROUND ECOSYSTEM
# ==========================================

class RoundActivity(db.Model):
    """
    Specific timeline events within a single round
    (e.g., 'Choice Filling', 'Seat Allocation Result')
    """
    __tablename__ = 'round_activities'

    id = db.Column(db.Integer, primary_key=True)
    # 🚨 FIXED: Points to 'counselling_rounds.id'
    round_id = db.Column(db.Integer, db.ForeignKey('counselling_rounds.id', ondelete='CASCADE'), nullable=False)

    activity_name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    is_actionable = db.Column(db.Boolean, default=False)

    # 🚨 FIXED: Points to 'CounsellingRound'
    round = db.relationship('CounsellingRound', backref=db.backref('activities', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<RoundActivity {self.activity_name}>"


class RoundArtifact(db.Model):
    """
    Flexible document storage for a round
    (e.g., 'Seat Matrix PDF', 'Cutoff Ranks')
    """
    __tablename__ = 'round_artifacts'

    id = db.Column(db.Integer, primary_key=True)
    # 🚨 FIXED: Points to 'counselling_rounds.id'
    round_id = db.Column(db.Integer, db.ForeignKey('counselling_rounds.id', ondelete='CASCADE'), nullable=False)

    document_name = db.Column(db.String(255), nullable=False)
    document_link = db.Column(db.String(1000), nullable=False)
    artifact_type = db.Column(db.String(50), nullable=True)

    # 🚨 FIXED: Points to 'CounsellingRound'
    round = db.relationship('CounsellingRound', backref=db.backref('artifacts', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<RoundArtifact {self.document_name}>"