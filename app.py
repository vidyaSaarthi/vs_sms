import os
import re
import json
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Staff, Student, Document, State, StateCategory, University, UniversityCategory, Exam, Counselling, Form, CounsellingRound, RoundSchedule, College, StudentCounsellingRegistration, StudentRoundResult, Course
from models import db, Staff, Student, Document, State, StateCategory, University, UniversityCategory, Exam, Counselling, Form, CounsellingRound, RoundSchedule, College, StudentCounsellingRegistration, StudentRoundResult, Course, StudentExamResult
from sqlalchemy.exc import IntegrityError
from datetime import date

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'vidyasaarthi_super_secret_key_2026'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vidyasaarthi.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['ADMIN_PIN'] = '2468'

app = Flask(__name__)

# Cloud-Safe Environment Variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vidyasaarthi_fallback_key')
app.config['ADMIN_PIN'] = os.environ.get('ADMIN_PIN', '8888')

# Smart Database Routing (Pure Python pg8000 driver)
db_url = os.environ.get('DATABASE_URL', 'sqlite:///vidyasaarthi.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 🚀 AUTOMATIC CLOUD DATABASE BUILDER
with app.app_context():
    db.create_all()
    if not Staff.query.filter_by(username='admin').first():
        db.session.add(Staff(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
        db.session.commit()
        print("✅ Master Admin account automatically injected!")



def convert_to_embed_link(url):
    if not url: return None
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if not match: match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match: return f"https://drive.google.com/file/d/{match.group(1)}/preview"
    return url


# ADDED '12th_admit_card' to the list
MASTER_DOC_TYPES = [
    'photo', 'student_signature', 'aadhaar_card', '10th_marksheet', '11th_marksheet', '12th_marksheet',
    'bank_proof', 'birth_certificate', 'residence_proof', 'caste_certificate', 'ews_certificate',
    'family_id', 'character_certificate', 'improvement_marksheet', 'neet_jee_result', 'passport',
    'school_leaving_certificate', 'transfer_certificate', 'father_aadhaar', 'mother_aadhaar',
    'neet_jee_admit_card', 'student_pan_card', 'apaar_id_doc', 'fingerprints', 'driving_license',
    '12th_admit_card'
]


@login_manager.user_loader
def load_user(user_id): return Staff.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # SECURITY FIX: If already logged in, skip the login page entirely
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user = Staff.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')


# ==========================================
# SECURITY: CHANGE PASSWORD
# ==========================================
@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')

    # 1. Verify current password
    if not check_password_hash(current_user.password_hash, current_pw):
        flash("Security Alert: Current password is incorrect.", "error")
        return redirect(request.referrer or url_for('dashboard'))

    # 2. Check if new passwords match
    if new_pw != confirm_pw:
        flash("Validation Error: New passwords do not match.", "error")
        return redirect(request.referrer or url_for('dashboard'))

    # 3. Hash and save the new password
    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()

    flash("Password updated successfully! Please log in with your new credentials.", "success")
    return redirect(url_for('logout'))  # Force login with new password

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


from flask import request, redirect, url_for, flash


# 1. Route to display the Master Data page
@app.route('/settings/master')
@login_required
def master_data():
    exams = Exam.query.order_by(Exam.name.asc()).all()
    states = State.query.order_by(State.name.asc()).all()
    universities = University.query.order_by(University.name.asc()).all()
    courses = Course.query.order_by(Course.name.asc()).all()  # Added this

    return render_template('master_data.html', exams=exams, states=states, universities=universities, courses=courses)


# ==========================================
# EDIT MASTER DATA (Exams, States, Unis, Courses)
# ==========================================
@app.route('/settings/master/edit/<data_type>/<int:item_id>', methods=['POST'])
@login_required
def edit_master_data(data_type, item_id):
    model_map = {'exam': Exam, 'state': State, 'university': University, 'course': Course}
    model = model_map.get(data_type)
    if not model:
        return redirect(url_for('master_data'))

    item = model.query.get_or_404(item_id)
    new_name = request.form.get('name')

    if new_name and new_name.strip():
        item.name = new_name.strip()
        db.session.commit()
        flash(f"Updated successfully to '{item.name}'!", "success")
    return redirect(url_for('master_data'))


# ==========================================
# EDIT ADMISSIONS DATA (Counselling)
# ==========================================
@app.route('/admissions/edit_counselling/<int:item_id>', methods=['POST'])
@login_required
def edit_counselling(item_id):
    c = Counselling.query.get_or_404(item_id)
    c.name = request.form.get('name')

    # Update type and target if changed
    c.counselling_type = request.form.get('counselling_type')
    target_id = request.form.get('target_id')
    c.state_id = target_id if c.counselling_type == 'State' else None
    c.university_id = target_id if c.counselling_type == 'University' else None

    # Update the Exam Link
    exam_id_val = request.form.get('exam_id')
    c.exam_id = int(exam_id_val) if exam_id_val else None

    db.session.commit()
    flash("Counselling process updated successfully!", "success")
    return redirect(url_for('admissions_hub'))


# ==========================================
# EDIT ADMISSIONS DATA (Forms & Admit Cards)
# ==========================================
@app.route('/admissions/edit_form/<int:item_id>', methods=['POST'])
@login_required
def edit_form(item_id):
    form = Form.query.get_or_404(item_id)
    try:
        form.name = request.form.get('name')

        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        form.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        form.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

        form.form_type = request.form.get('form_type')
        target_id = request.form.get('target_id')
        form.exam_id = target_id if form.form_type == 'Exam' else None
        form.counselling_id = target_id if form.form_type == 'Counselling' else None

        # NEW LOGIC: Only update Admit Card if it's an Exam
        if form.form_type == 'Exam':
            admit_date_str = request.form.get('admit_card_date')
            form.admit_card_date = datetime.strptime(admit_date_str, '%Y-%m-%d').date() if admit_date_str else None
            form.admit_card_link = request.form.get('admit_card_link')
        else:
            form.admit_card_date = None
            form.admit_card_link = None

        def safe_float(val): return float(val) if val and val.strip() else None
        form.fee_general = safe_float(request.form.get('fee_general'))
        form.fee_obc = safe_float(request.form.get('fee_obc'))
        form.fee_sc_st = safe_float(request.form.get('fee_sc_st'))
        form.fee_female = safe_float(request.form.get('fee_female'))

        form.document_link = request.form.get('document_link')

        db.session.commit()
        flash("Form details updated!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating form: {str(e)}", "error")

    return redirect(url_for('admissions_hub'))


# 2. Universal Route to process new additions
@app.route('/settings/master/add', methods=['POST'])
@login_required
def add_master_data():
    data_type = request.form.get('data_type')
    name = request.form.get('name')

    if not name:
        flash("Name cannot be empty!", "error")
        return redirect(url_for('master_data'))

    try:
        if data_type == 'exam':
            new_entry = Exam(name=name)
            db.session.add(new_entry)
            flash(f"Exam '{name}' added successfully!", "success")

        elif data_type == 'state':
            new_entry = State(name=name)
            db.session.add(new_entry)
            flash(f"State '{name}' added successfully!", "success")

        elif data_type == 'university':
            new_entry = University(name=name)
            db.session.add(new_entry)
            flash(f"University '{name}' added successfully!", "success")

        elif data_type == 'course':
            new_entry = Course(name=name)
            db.session.add(new_entry)
            flash(f"Course '{name}' added successfully!", "success")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("Error saving data. It might already exist.", "error")

    return redirect(url_for('master_data'))


from flask import request, redirect, url_for, flash
from datetime import datetime


# ==========================================
# ADMISSIONS HUB (MASTER DATA)
# ==========================================
@app.route('/admissions')
@login_required
def admissions_hub():
    today = date.today().strftime('%Y-%m-%d')

    # 1. Split Forms by Type
    all_forms = Form.query.order_by(Form.end_date.asc()).all()
    exam_forms = [f for f in all_forms if f.form_type == 'Exam']
    counselling_forms_list = [f for f in all_forms if f.form_type == 'Counselling']

    # 1b. Group Counselling Forms by Exam
    counselling_forms_grouped = {}
    for form in counselling_forms_list:
        exam_name = "Independent / Unlinked Processes"
        if form.counselling_id:
            couns = Counselling.query.get(form.counselling_id)
            if couns and couns.exam_id:
                exam = Exam.query.get(couns.exam_id)
                if exam:
                    exam_name = exam.name

        if exam_name not in counselling_forms_grouped:
            counselling_forms_grouped[exam_name] = []
        counselling_forms_grouped[exam_name].append(form)

    # 2. Group Master Counselling Processes by Exam
    all_counsellings = Counselling.query.order_by(Counselling.name.asc()).all()
    counselling_grouped = {}
    for c in all_counsellings:
        exam_name = c.exam.name if c.exam else "Independent / Unlinked Processes"
        if exam_name not in counselling_grouped:
            counselling_grouped[exam_name] = []
        counselling_grouped[exam_name].append(c)

    # 3. Master Dropdown Data
    exams = Exam.query.order_by(Exam.name.asc()).all()
    states = State.query.order_by(State.name.asc()).all()
    universities = University.query.order_by(University.name.asc()).all()

    return render_template('admissions.html',
                           forms=all_forms,  # Kept for modal loops
                           exam_forms=exam_forms,
                           counselling_forms_grouped=counselling_forms_grouped,  # <-- Passed grouped forms
                           counsellings=all_counsellings,  # Kept for modal loops
                           counselling_grouped=counselling_grouped,
                           exams=exams,
                           states=states,
                           universities=universities,
                           today=today)

# 2. Add New Counselling Process
@app.route('/admissions/add_counselling', methods=['POST'])
@login_required
def add_counselling():
    name = request.form.get('name')
    counselling_type = request.form.get('counselling_type')
    target_id = request.form.get('target_id')
    exam_id_val = request.form.get('exam_id') # <-- Grab the Exam

    new_counselling = Counselling(
        name=name,
        counselling_type=counselling_type,
        state_id=target_id if counselling_type == 'State' else None,
        university_id=target_id if counselling_type == 'University' else None,
        exam_id=int(exam_id_val) if exam_id_val else None # <-- Save it
    )
    db.session.add(new_counselling)
    db.session.commit()
    flash(f"Counselling process '{name}' created successfully!", "success")
    return redirect(url_for('admissions_hub'))


# 3. Add New Form / Deadline
@app.route('/admissions/add_form', methods=['POST'])
@login_required
def add_form():
    name = request.form.get('name')
    form_type = request.form.get('form_type')
    target_id = request.form.get('target_id')

    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

    # NEW LOGIC: Only process Admit Cards if it's an Exam
    if form_type == 'Exam':
        admit_date_str = request.form.get('admit_card_date')
        admit_card_date = datetime.strptime(admit_date_str, '%Y-%m-%d').date() if admit_date_str else None
        admit_card_link = request.form.get('admit_card_link')
    else:
        admit_card_date = None
        admit_card_link = None

    def safe_float(val): return float(val) if val and val.strip() else None

    new_form = Form(
        name=name,
        form_type=form_type,
        exam_id=target_id if form_type == 'Exam' else None,
        counselling_id=target_id if form_type == 'Counselling' else None,
        start_date=start_date,
        end_date=end_date,
        admit_card_date=admit_card_date,
        admit_card_link=admit_card_link,
        fee_general=safe_float(request.form.get('fee_general')),
        fee_obc=safe_float(request.form.get('fee_obc')),
        fee_sc_st=safe_float(request.form.get('fee_sc_st')),
        fee_female=safe_float(request.form.get('fee_female')),
        document_link=request.form.get('document_link')
    )
    db.session.add(new_form)
    db.session.commit()
    flash(f"Form tracking for '{name}' added successfully!", "success")
    return redirect(url_for('admissions_hub'))


@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # 1. Gather Student KPIs
    total_students = Student.query.count()
    pending_students = Student.query.filter_by(is_approved=False).count()

    # 2. Gather Admissions KPIs
    total_forms = Form.query.count()
    active_counselling = Counselling.query.count()

    today = date.today()

    # 3. Get Upcoming EXAM Deadlines (Limit to 5 for neatness)
    upcoming_exam_forms = Form.query.filter(
        Form.end_date >= today,
        Form.form_type == 'Exam'
    ).order_by(Form.end_date.asc()).limit(5).all()

    # 4. Get Upcoming COUNSELLING Deadlines and Group by Exam
    upcoming_couns_forms = Form.query.filter(
        Form.end_date >= today,
        Form.form_type == 'Counselling'
    ).order_by(Form.end_date.asc()).all()

    counselling_grouped = {}
    for form in upcoming_couns_forms:
        exam_name = "Independent / Unlinked Processes"

        # Safely find the linked Exam Name
        if form.counselling_id:
            couns = Counselling.query.get(form.counselling_id)
            if couns and couns.exam_id:
                exam = Exam.query.get(couns.exam_id)
                if exam:
                    exam_name = exam.name

        # Add the form to the correct Exam group
        if exam_name not in counselling_grouped:
            counselling_grouped[exam_name] = []
        counselling_grouped[exam_name].append(form)

    # 5. Get Recently Added Students
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_students=total_students,
                           pending_students=pending_students,
                           total_forms=total_forms,
                           active_counselling=active_counselling,
                           upcoming_exam_forms=upcoming_exam_forms,  # <-- Passed to HTML
                           counselling_grouped=counselling_grouped,  # <-- Passed to HTML
                           recent_students=recent_students)


def extract_dynamic_marks(prefix, group):
    names = request.form.getlist(f'{prefix}_{group}_name[]')
    maxs = request.form.getlist(f'{prefix}_{group}_max[]')
    obts = request.form.getlist(f'{prefix}_{group}_obt[]')
    return [{"name": n, "max": m, "obt": o} for n, m, o in zip(names, maxs, obts) if n.strip()]


@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        emails = [e.strip().lower() for e in [request.form.get('email_address'), request.form.get('alt_email'),
                                              request.form.get('emergency_email')] if e and e.strip()]
        if len(emails) != len(set(emails)):
            flash("Validation Error: All provided email addresses must be unique.")
            return render_template('add_student.html')

        phones = [p.strip() for p in [request.form.get('mobile_number'), request.form.get('alt_mobile_number'),
                                      request.form.get('emergency_mobile')] if p and p.strip()]
        if len(phones) != len(set(phones)):
            flash("Validation Error: All provided phone numbers must be strictly different.")
            return render_template('add_student.html')

        try:
            dob_str = request.form.get('dob')
            dob_val = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
            c10_issue = request.form.get('class_10_issue_date')
            c10_issue_val = datetime.strptime(c10_issue, '%Y-%m-%d').date() if c10_issue else None
            c12_issue = request.form.get('class_12_issue_date')
            c12_issue_val = datetime.strptime(c12_issue, '%Y-%m-%d').date() if c12_issue else None
            forms_filled_str = ", ".join(request.form.getlist('forms_filled'))

            c10_marks = {
                "main": {
                    "eng": {"max": request.form.get('c10_main_eng_max'), "obt": request.form.get('c10_main_eng_obt')},
                    "math": {"max": request.form.get('c10_main_math_max'),
                             "obt": request.form.get('c10_main_math_obt')},
                    "sci": {"max": request.form.get('c10_main_sci_max'), "obt": request.form.get('c10_main_sci_obt')},
                    "sst": {"max": request.form.get('c10_main_sst_max'), "obt": request.form.get('c10_main_sst_obt')}
                },
                "other": {"subjects": extract_dynamic_marks('c10', 'other')},
                "additional": {"subjects": extract_dynamic_marks('c10', 'add')},
                "overall_main": {"max": request.form.get('c10_overall_main_max'),
                                 "obt": request.form.get('c10_overall_main_obt'),
                                 "perc": request.form.get('c10_overall_main_perc')},
                "overall_grand": {"max": request.form.get('c10_overall_grand_max'),
                                  "obt": request.form.get('c10_overall_grand_obt'),
                                  "perc": request.form.get('c10_overall_grand_perc')}
            }

            c12_marks = {
                "main": {
                    "eng": {"max": request.form.get('c12_main_eng_max'), "obt": request.form.get('c12_main_eng_obt')},
                    "phy": {"max": request.form.get('c12_main_phy_max'), "obt": request.form.get('c12_main_phy_obt')},
                    "chem": {"max": request.form.get('c12_main_chem_max'), "obt": request.form.get('c12_main_chem_obt')}
                },
                "other": {"subjects": extract_dynamic_marks('c12', 'other')},
                "additional": {"subjects": extract_dynamic_marks('c12', 'add')},
                "overall_main": {"max": request.form.get('c12_overall_main_max'),
                                 "obt": request.form.get('c12_overall_main_obt'),
                                 "perc": request.form.get('c12_overall_main_perc')},
                "overall_grand": {"max": request.form.get('c12_overall_grand_max'),
                                  "obt": request.form.get('c12_overall_grand_obt'),
                                  "perc": request.form.get('c12_overall_grand_perc')}
            }

            new_student = Student(
                exam_type=request.form.get('exam_type'), forms_filled=forms_filled_str,
                other_forms_filled=request.form.get('other_forms_filled'),
                full_name=request.form.get('full_name'), dob=dob_val, gender=request.form.get('gender'),
                blood_group=request.form.get('blood_group'), religion=request.form.get('religion'),  # NEW
                category=request.form.get('category'), identification_mark=request.form.get('identification_mark'),
                aadhaar_no=request.form.get('aadhaar_no'), nationality=request.form.get('nationality'),
                nativity=request.form.get('nativity'),
                mobile_number=request.form.get('mobile_number'),
                alt_mobile_number=request.form.get('alt_mobile_number'),
                emergency_mobile=request.form.get('emergency_mobile'),
                email_address=request.form.get('email_address'), alt_email=request.form.get('alt_email'),
                emergency_email=request.form.get('emergency_email'),
                house_no=request.form.get('house_no'), street_name=request.form.get('street_name'),
                post_office=request.form.get('post_office'),
                pin_code=request.form.get('pin_code'), state_ut=request.form.get('state_ut'),
                district=request.form.get('district'),

                father_name=request.form.get('father_name'), father_aadhaar_no=request.form.get('father_aadhaar_no'),
                father_education=request.form.get('father_education'),
                father_occupation=request.form.get('father_occupation'),
                father_designation=request.form.get('father_designation'),
                father_organization=request.form.get('father_organization'),  # NEW

                mother_name=request.form.get('mother_name'), mother_aadhaar_no=request.form.get('mother_aadhaar_no'),
                mother_education=request.form.get('mother_education'),
                mother_occupation=request.form.get('mother_occupation'),
                mother_designation=request.form.get('mother_designation'),
                mother_organization=request.form.get('mother_organization'),  # NEW

                family_income=request.form.get('family_income'), bank_holder_name=request.form.get('bank_holder_name'),
                bank_name=request.form.get('bank_name'),
                bank_branch=request.form.get('bank_branch'), bank_address=request.form.get('bank_address'),
                bank_account_no=request.form.get('bank_account_no'), bank_ifsc=request.form.get('bank_ifsc'),

                class_10_year=request.form.get('class_10_year') or None,
                class_10_school=request.form.get('class_10_school'),
                class_10_school_type=request.form.get('class_10_school_type'),
                class_10_state=request.form.get('class_10_state'),  # NEW
                class_10_serial=request.form.get('class_10_serial'),
                class_10_reg_no=request.form.get('class_10_reg_no'),
                class_10_board=request.form.get('class_10_board'), class_10_issue_date=c10_issue_val,
                class_10_roll_no=request.form.get('class_10_roll_no'),
                class_10_marks_data=json.dumps(c10_marks),

                class_11_year=request.form.get('class_11_year') or None,
                class_11_school=request.form.get('class_11_school'),
                class_11_state=request.form.get('class_11_state'),
                class_11_roll_no=request.form.get('class_11_roll_no'),

                passed_appearing=request.form.get('passed_appearing'),
                studied_sanskrit=request.form.get('studied_sanskrit'),
                registration_no_apaar_id=request.form.get('registration_no_apaar_id'),
                class_12_year=request.form.get('class_12_year') or None,
                class_12_school=request.form.get('class_12_school'),
                class_12_school_type=request.form.get('class_12_school_type'),  # NEW
                class_12_school_code=request.form.get('class_12_school_code'),
                class_12_center_code=request.form.get('class_12_center_code'),  # NEW
                class_12_state=request.form.get('class_12_state'), class_12_serial=request.form.get('class_12_serial'),
                class_12_reg_no=request.form.get('class_12_reg_no'), class_12_board=request.form.get('class_12_board'),
                class_12_issue_date=c12_issue_val, class_12_roll_no=request.form.get('class_12_roll_no'),
                class_12_admit_card_id=request.form.get('class_12_admit_card_id'),  # NEW
                class_12_marks_data=json.dumps(c12_marks),
                created_by = request.form.get('created_by'),
                academic_status=request.form.get('academic_status', 'Fresher'),
            )
            db.session.add(new_student)
            db.session.flush()

            for doc_type in MASTER_DOC_TYPES:
                raw_link = request.form.get(f"{doc_type}_url")
                if raw_link and raw_link.strip():
                    db.session.add(Document(student_id=new_student.id, doc_type=doc_type,
                                            drive_link=convert_to_embed_link(raw_link.strip())))

            custom_names = request.form.getlist('custom_doc_name[]')
            custom_urls = request.form.getlist('custom_doc_url[]')
            for name, url in zip(custom_names, custom_urls):
                if name and name.strip() and url and url.strip():
                    db.session.add(Document(student_id=new_student.id, doc_type=name.strip(),
                                            drive_link=convert_to_embed_link(url.strip())))

            db.session.commit()
            flash(f"Student {new_student.full_name} added successfully!")
            return redirect(url_for('dashboard'))

        except IntegrityError:
            db.session.rollback()
            flash("Error: Duplicate Aadhaar or Mobile Number detected.")
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving student: {str(e)}")

    return render_template('add_student.html')


# 1. Register Student for a Counselling Process
# ==========================================
# ADMISSIONS JOURNEY: REGISTER/PLAN COUNSELLING
# ==========================================
@app.route('/student/<int:student_id>/register_counselling', methods=['POST'])
@login_required
def register_student_counselling(student_id):
    try:
        counselling_id = request.form.get('counselling_id')
        app_no = request.form.get('application_number')
        reg_status = request.form.get('registration_status', 'Planned')

        registration = StudentCounsellingRegistration(
            student_id=student_id,
            counselling_id=counselling_id,
            registration_status=reg_status,
            application_number=app_no if app_no and app_no.strip() else None,
            login_username=request.form.get('login_username'),
            login_password=request.form.get('login_password'),
            registered_email=request.form.get('registered_email'),
            registered_mobile=request.form.get('registered_mobile'), # <-- NEW FIELD
            form_confirmation_link=request.form.get('form_confirmation_link'),
            registration_date=date.today()
        )
        db.session.add(registration)
        db.session.commit()
        flash(f"Counselling process marked as {reg_status}!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error registering process: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))


# ==========================================
# ADMISSIONS JOURNEY: DELETE COUNSELLING REGISTRATION
# ==========================================
@app.route('/student/delete_counselling_reg/<int:reg_id>', methods=['POST'])
@login_required
def delete_counselling_reg(reg_id):
    reg = StudentCounsellingRegistration.query.get_or_404(reg_id)
    student_id = reg.student_id
    counselling_name = reg.counselling.name

    try:
        # Step 1: Clean up any saved Round Results for this specific counselling process
        associated_rounds = StudentRoundResult.query.join(CounsellingRound).filter(
            StudentRoundResult.student_id == student_id,
            CounsellingRound.counselling_id == reg.counselling_id
        ).all()

        for res in associated_rounds:
            db.session.delete(res)

        # Step 2: Delete the registration itself
        db.session.delete(reg)
        db.session.commit()

        flash(f"Removed {counselling_name} from the student's journey.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing participation: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))

# 2. Record Round Result


@app.route('/student/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        if student.is_approved:
            if request.form.get('admin_pin') != app.config['ADMIN_PIN']:
                flash("SECURITY BLOCK: Invalid Admin PIN. This record has been Parent Approved and is locked.")
                return redirect(url_for('edit_student', id=student.id))

        emails = [e.strip().lower() for e in [request.form.get('email_address'), request.form.get('alt_email'),
                                              request.form.get('emergency_email')] if e and e.strip()]
        if len(emails) != len(set(emails)):
            flash("Validation Error: All provided email addresses must be unique.")
            return redirect(url_for('edit_student', id=student.id))

        phones = [p.strip() for p in [request.form.get('mobile_number'), request.form.get('alt_mobile_number'),
                                      request.form.get('emergency_mobile')] if p and p.strip()]
        if len(phones) != len(set(phones)):
            flash("Validation Error: All provided phone numbers must be strictly different.")
            return redirect(url_for('edit_student', id=student.id))

        try:
            dob_str = request.form.get('dob')
            student.dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None

            c10_issue = request.form.get('class_10_issue_date')
            student.class_10_issue_date = datetime.strptime(c10_issue, '%Y-%m-%d').date() if c10_issue else None

            c12_issue = request.form.get('class_12_issue_date')
            student.class_12_issue_date = datetime.strptime(c12_issue, '%Y-%m-%d').date() if c12_issue else None

            student.forms_filled = ", ".join(request.form.getlist('forms_filled'))
            student.other_forms_filled = request.form.get('other_forms_filled')

            c10_marks = {
                "main": {
                    "eng": {"max": request.form.get('c10_main_eng_max'), "obt": request.form.get('c10_main_eng_obt')},
                    "math": {"max": request.form.get('c10_main_math_max'),
                             "obt": request.form.get('c10_main_math_obt')},
                    "sci": {"max": request.form.get('c10_main_sci_max'), "obt": request.form.get('c10_main_sci_obt')},
                    "sst": {"max": request.form.get('c10_main_sst_max'), "obt": request.form.get('c10_main_sst_obt')}
                },
                "other": {"subjects": extract_dynamic_marks('c10', 'other')},
                "additional": {"subjects": extract_dynamic_marks('c10', 'add')},
                "overall_main": {"max": request.form.get('c10_overall_main_max'),
                                 "obt": request.form.get('c10_overall_main_obt'),
                                 "perc": request.form.get('c10_overall_main_perc')},
                "overall_grand": {"max": request.form.get('c10_overall_grand_max'),
                                  "obt": request.form.get('c10_overall_grand_obt'),
                                  "perc": request.form.get('c10_overall_grand_perc')}
            }

            c12_marks = {
                "main": {
                    "eng": {"max": request.form.get('c12_main_eng_max'), "obt": request.form.get('c12_main_eng_obt')},
                    "phy": {"max": request.form.get('c12_main_phy_max'), "obt": request.form.get('c12_main_phy_obt')},
                    "chem": {"max": request.form.get('c12_main_chem_max'), "obt": request.form.get('c12_main_chem_obt')}
                },
                "other": {"subjects": extract_dynamic_marks('c12', 'other')},
                "additional": {"subjects": extract_dynamic_marks('c12', 'add')},
                "overall_main": {"max": request.form.get('c12_overall_main_max'),
                                 "obt": request.form.get('c12_overall_main_obt'),
                                 "perc": request.form.get('c12_overall_main_perc')},
                "overall_grand": {"max": request.form.get('c12_overall_grand_max'),
                                  "obt": request.form.get('c12_overall_grand_obt'),
                                  "perc": request.form.get('c12_overall_grand_perc')}
            }

            student.exam_type = request.form.get('exam_type')
            student.full_name = request.form.get('full_name')
            student.gender = request.form.get('gender')
            student.blood_group = request.form.get('blood_group')  # NEW
            student.religion = request.form.get('religion')  # NEW
            student.category = request.form.get('category')
            student.identification_mark = request.form.get('identification_mark')
            student.aadhaar_no = request.form.get('aadhaar_no')
            student.nationality = request.form.get('nationality')
            student.nativity = request.form.get('nativity')
            student.mobile_number = request.form.get('mobile_number')
            student.alt_mobile_number = request.form.get('alt_mobile_number')
            student.emergency_mobile = request.form.get('emergency_mobile')
            student.email_address = request.form.get('email_address')
            student.alt_email = request.form.get('alt_email')
            student.emergency_email = request.form.get('emergency_email')
            student.house_no = request.form.get('house_no')
            student.street_name = request.form.get('street_name')
            student.post_office = request.form.get('post_office')
            student.pin_code = request.form.get('pin_code')
            student.state_ut = request.form.get('state_ut')
            student.district = request.form.get('district')

            student.father_name = request.form.get('father_name')
            student.father_aadhaar_no = request.form.get('father_aadhaar_no')
            student.father_education = request.form.get('father_education')
            student.father_occupation = request.form.get('father_occupation')
            student.father_designation = request.form.get('father_designation')  # NEW
            student.father_organization = request.form.get('father_organization')  # NEW

            student.mother_name = request.form.get('mother_name')
            student.mother_aadhaar_no = request.form.get('mother_aadhaar_no')
            student.mother_education = request.form.get('mother_education')
            student.mother_occupation = request.form.get('mother_occupation')
            student.mother_designation = request.form.get('mother_designation')  # NEW
            student.mother_organization = request.form.get('mother_organization')  # NEW

            student.family_income = request.form.get('family_income')
            student.bank_holder_name = request.form.get('bank_holder_name')
            student.bank_name = request.form.get('bank_name')
            student.bank_branch = request.form.get('bank_branch')
            student.bank_address = request.form.get('bank_address')
            student.bank_account_no = request.form.get('bank_account_no')
            student.bank_ifsc = request.form.get('bank_ifsc')

            student.class_10_year = request.form.get('class_10_year') or None
            student.class_10_school = request.form.get('class_10_school')
            student.class_10_school_type = request.form.get('class_10_school_type')  # NEW
            student.class_10_state = request.form.get('class_10_state')
            student.class_10_serial = request.form.get('class_10_serial')
            student.class_10_reg_no = request.form.get('class_10_reg_no')
            student.class_10_board = request.form.get('class_10_board')
            student.class_10_roll_no = request.form.get('class_10_roll_no')
            student.class_10_marks_data = json.dumps(c10_marks)

            student.class_11_year = request.form.get('class_11_year') or None
            student.class_11_school = request.form.get('class_11_school')
            student.class_11_state = request.form.get('class_11_state')
            student.class_11_roll_no = request.form.get('class_11_roll_no')

            student.passed_appearing = request.form.get('passed_appearing')
            student.studied_sanskrit = request.form.get('studied_sanskrit')
            student.registration_no_apaar_id = request.form.get('registration_no_apaar_id')
            student.class_12_year = request.form.get('class_12_year') or None
            student.class_12_school = request.form.get('class_12_school')
            student.class_12_school_type = request.form.get('class_12_school_type')  # NEW
            student.class_12_school_code = request.form.get('class_12_school_code')  # NEW
            student.class_12_center_code = request.form.get('class_12_center_code')  # NEW
            student.class_12_state = request.form.get('class_12_state')
            student.class_12_serial = request.form.get('class_12_serial')
            student.class_12_reg_no = request.form.get('class_12_reg_no')
            student.class_12_board = request.form.get('class_12_board')
            student.class_12_roll_no = request.form.get('class_12_roll_no')
            student.class_12_admit_card_id = request.form.get('class_12_admit_card_id')  # NEW
            student.class_12_marks_data = json.dumps(c12_marks)
            student.created_by = request.form.get('created_by')
            student.academic_status = request.form.get('academic_status')

            for doc_type in MASTER_DOC_TYPES:
                raw_link = request.form.get(f"{doc_type}_url")
                embed_link = convert_to_embed_link(raw_link.strip()) if raw_link and raw_link.strip() else None
                existing_doc = Document.query.filter_by(student_id=student.id, doc_type=doc_type).first()
                if existing_doc:
                    if embed_link:
                        existing_doc.drive_link = embed_link
                    else:
                        db.session.delete(existing_doc)
                elif embed_link:
                    db.session.add(Document(student_id=student.id, doc_type=doc_type, drive_link=embed_link))

            old_custom_docs = Document.query.filter(Document.student_id == student.id,
                                                    Document.doc_type.notin_(MASTER_DOC_TYPES)).all()
            for od in old_custom_docs: db.session.delete(od)

            custom_names = request.form.getlist('custom_doc_name[]')
            custom_urls = request.form.getlist('custom_doc_url[]')
            for name, url in zip(custom_names, custom_urls):
                if name and name.strip() and url and url.strip():
                    db.session.add(Document(student_id=student.id, doc_type=name.strip(),
                                            drive_link=convert_to_embed_link(url.strip())))

            db.session.commit()
            flash(f"Student {student.full_name} updated successfully!")
            return redirect(url_for('view_student', id=student.id))


        except IntegrityError as e:

            db.session.rollback()

            # This prints the EXACT SQL error to your Railway/Terminal logs

            print(f"🚨 INTEGRITY ERROR DETAILS: {str(e.orig)}")

            flash("Database Error: A required field is missing or duplicated. Check your terminal logs for details.",
                  "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating student: {str(e)}")

    c10_marks = json.loads(student.class_10_marks_data) if student.class_10_marks_data else {"main": {},
                                                                                             "other": {"subjects": []},
                                                                                             "additional": {
                                                                                                 "subjects": []},
                                                                                             "overall_main": {},
                                                                                             "overall_grand": {}}
    c12_marks = json.loads(student.class_12_marks_data) if student.class_12_marks_data else {"main": {},
                                                                                             "other": {"subjects": []},
                                                                                             "additional": {
                                                                                                 "subjects": []},
                                                                                             "overall_main": {},
                                                                                             "overall_grand": {}}
    docs = {doc.doc_type: doc.drive_link.replace('/preview', '/view') if doc.drive_link else '' for doc in
            student.documents}
    forms_filled_list = [f.strip() for f in student.forms_filled.split(",")] if student.forms_filled else []

    custom_docs = Document.query.filter(Document.student_id == student.id,
                                        Document.doc_type.notin_(MASTER_DOC_TYPES)).all()

    return render_template('edit_student.html', student=student, c10_marks=c10_marks, c12_marks=c12_marks, docs=docs,
                           forms_filled_list=forms_filled_list, custom_docs=custom_docs)


@app.route('/student/<int:id>/approve', methods=['POST'])
@login_required
def approve_student(id):
    student = Student.query.get_or_404(id)
    student.is_approved = True
    db.session.commit()
    flash(f"🔒 Security Lock Active! {student.full_name}'s record has been marked as Parent Approved.")
    return redirect(url_for('view_student', id=student.id))


@app.route('/colleges')
@login_required
def college_directory():
    # 1. Get search and filter parameters
    search_query = request.args.get('search', '')
    state_filter = request.args.get('state_id', '')
    course_filter = request.args.get('course_id', '')  # <--- Make sure this is 'course_id'
    type_filter = request.args.get('type', '')

    # 2. Build the query
    query = College.query
    if search_query:
        query = query.filter(College.name.ilike(f'%{search_query}%'))
    if state_filter:
        query = query.filter(College.state_id == state_filter)
    if course_filter: # ADD THIS BLOCK to make the course search work
        query = query.filter(College.course_id == course_filter)
    if type_filter:
        query = query.filter(College.college_type == type_filter)

    colleges = query.order_by(College.name.asc()).all()

    # 3. Master data
    states = State.query.order_by(State.name.asc()).all()
    universities = University.query.order_by(University.name.asc()).all()
    courses = Course.query.order_by(Course.name.asc()).all()

    return render_template('colleges.html',
                           colleges=colleges,
                           states=states,
                           universities=universities,
                           courses=courses,
                           search_query=search_query,
                           state_filter=state_filter,
                           course_filter=course_filter, # <--- Pass this back to the HTML
                           type_filter=type_filter)

@app.route('/colleges/add', methods=['POST'])
@login_required  # Recommended to keep this secure
def add_college():
    try:
        # Get the ID from the dropdown, not text
        course_id_val = request.form.get('course_id')

        new_college = College(
            name=request.form.get('name'),
            college_type=request.form.get('college_type'),
            established_year=request.form.get('established_year'),
            state_id=request.form.get('state_id'),
            university_id=request.form.get('university_id'),
            course_id=int(course_id_val) if course_id_val else None,  # SAVING THE ID
            fees=request.form.get('fees'),
            service_bond=request.form.get('service_bond'),
            discontinued_bond=request.form.get('discontinued_bond'),
            college_information=request.form.get('college_information'),
            joining_documents=request.form.get('joining_documents')
        )
        db.session.add(new_college)
        db.session.commit()
        flash(f"College '{new_college.name}' added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving college: {str(e)}", "error")

    return redirect(url_for('college_directory'))


@app.route('/student/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    if request.form.get('admin_pin') == app.config['ADMIN_PIN']:
        Document.query.filter_by(student_id=student.id).delete()
        student_name = student.full_name
        db.session.delete(student)
        db.session.commit()
        flash(f"🗑️ Record Deleted: {student_name} has been permanently removed.")
        return redirect(url_for('dashboard'))
    else:
        flash("SECURITY BLOCK: Invalid Admin PIN.")
        return redirect(url_for('view_student', id=student.id))


@app.route('/student/<int:id>')
@login_required
def view_student(id):
    student = Student.query.get_or_404(id)
    active_counsellings = Counselling.query.all()
    exams = Exam.query.order_by(Exam.name.asc()).all()  # Fetch Master Exams
    return render_template('profile.html', student=student, active_counsellings=active_counsellings, exams=exams)


@app.route('/student/<int:id>/export')
@login_required
def export_verification(id):
    student = Student.query.get_or_404(id)
    c10_marks = json.loads(student.class_10_marks_data) if student.class_10_marks_data else {"main": {},
                                                                                             "other": {"subjects": []},
                                                                                             "additional": {
                                                                                                 "subjects": []},
                                                                                             "overall_main": {},
                                                                                             "overall_grand": {}}
    c12_marks = json.loads(student.class_12_marks_data) if student.class_12_marks_data else {"main": {},
                                                                                             "other": {"subjects": []},
                                                                                             "additional": {
                                                                                                 "subjects": []},
                                                                                             "overall_main": {},
                                                                                             "overall_grand": {}}
    return render_template('verification_sheet.html', student=student, c10_marks=c10_marks, c12_marks=c12_marks,
                           master_docs=MASTER_DOC_TYPES)


@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not Staff.query.filter_by(username='admin').first():
        db.session.add(Staff(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
        db.session.commit()
        print("Database initialized! Default login is admin / admin123")

from flask import request, render_template


@app.route('/students')
@login_required
def student_pipeline():
    search_query = request.args.get('search', '')
    exam_filter = request.args.get('exam', '')
    counsellor_filter = request.args.get('counsellor', '')
    status_filter = request.args.get('status', '')
    counselling_filter = request.args.get('counselling', '')  # <-- NEW FILTER

    query = Student.query

    if search_query:
        query = query.filter(
            db.or_(
                Student.full_name.ilike(f'%{search_query}%'),
                Student.mobile_number.ilike(f'%{search_query}%'),
                Student.aadhaar_no.ilike(f'%{search_query}%')
            )
        )

    if exam_filter:
        query = query.filter(Student.exam_type == exam_filter)

    if counsellor_filter:
        query = query.filter(Student.created_by == counsellor_filter)

    if status_filter:
        query = query.filter(Student.academic_status == status_filter)

    # NEW: Filter students who have a registration matching the ID
    if counselling_filter:
        query = query.join(StudentCounsellingRegistration).filter(
            StudentCounsellingRegistration.counselling_id == int(counselling_filter)
        )

    counsellors = db.session.query(Student.created_by).distinct().filter(Student.created_by != None).all()
    counsellor_list = [c[0] for c in counsellors]

    # NEW: Fetch counselling processes for the dropdown menu
    active_counsellings = Counselling.query.order_by(Counselling.name.asc()).all()

    students = query.order_by(Student.created_at.desc()).all()

    return render_template('students.html',
                           students=students,
                           search_query=search_query,
                           exam_filter=exam_filter,
                           counsellor_filter=counsellor_filter,
                           status_filter=status_filter,
                           counselling_filter=counselling_filter,  # <-- Added to template
                           counsellors=counsellor_list,
                           active_counsellings=active_counsellings)  # <-- Added to template


# ==========================================
# UNIVERSAL MASTER DATA DELETE
# ==========================================
@app.route('/settings/master/delete/<data_type>/<int:item_id>', methods=['POST'])
@login_required
def delete_master_data(data_type, item_id):
    # Map the string from the URL to the actual Python Class
    model_map = {
        'exam': Exam,
        'state': State,
        'university': University,
        'course': Course
    }

    model = model_map.get(data_type)
    if not model:
        return redirect(url_for('master_data'))

    item = model.query.get_or_404(item_id)
    item_name = item.name

    try:
        db.session.delete(item)
        db.session.commit()
        flash(f"Deleted '{item_name}' successfully!", "success")
    except IntegrityError:
        db.session.rollback()
        flash(f"⚠️ Cannot delete '{item_name}' because it is actively being used by a College or Student record.",
              "error")

    return redirect(url_for('master_data'))


## ==========================================
# ADMISSIONS DATA DELETE
# ==========================================
@app.route('/admissions/delete/counselling/<int:item_id>', methods=['POST'])
@login_required
def delete_counselling_record(item_id):
    item = Counselling.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Counselling process deleted.", "success")
    except Exception as e:
        db.session.rollback()

        # Capture the actual Postgres Database Error
        error_str = str(e).lower()

        # Translate the ugly SQL error into a human-readable ERP instruction
        if 'forms' in error_str:
            flash("⚠️ Cannot delete: There is a Form/Deadline linked to this process. Please delete or edit the Form first.", error_str)
        elif 'student_counselling_registrations' in error_str:
            flash("⚠️ Cannot delete: There is still at least one student registered for this process.", error_str)
        else:
            flash(f"⚠️ Cannot delete due to database constraint.", error_str)

    return redirect(url_for('admissions_hub'))


@app.route('/admissions/delete/form/<int:item_id>', methods=['POST'])
@login_required
def delete_form_record(item_id):
    item = Form.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Form deadline removed.", "success")
    return redirect(url_for('admissions_hub'))


# ==========================================
# ADMISSIONS JOURNEY: SAVE EXAM RESULT
# ==========================================
@app.route('/student/<int:student_id>/add_exam_result', methods=['POST'])
@login_required
def add_exam_result(student_id):
    score_val = request.form.get('score')
    percentile_val = request.form.get('percentile')
    air_val = request.form.get('all_india_rank')
    state_rank_val = request.form.get('state_rank')

    try:
        result = StudentExamResult(
            student_id=student_id,
            exam_id=request.form.get('exam_id'),
            application_number=request.form.get('application_number'),
            score=float(score_val) if score_val else None,
            percentile=float(percentile_val) if percentile_val else None,
            all_india_rank=int(air_val) if air_val else None,
            state_rank=int(state_rank_val) if state_rank_val else None
        )
        db.session.add(result)
        db.session.commit()
        flash("Exam result added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving exam result: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))


# ==========================================
# ADMISSIONS JOURNEY: EDIT EXAM RESULT
# ==========================================
@app.route('/student/edit_exam_result/<int:result_id>', methods=['POST'])
@login_required
def edit_exam_result(result_id):
    result = StudentExamResult.query.get_or_404(result_id)
    student_id = result.student_id

    try:
        result.exam_id = request.form.get('exam_id')
        result.application_number = request.form.get('application_number')

        score_val = request.form.get('score')
        percentile_val = request.form.get('percentile')
        air_val = request.form.get('all_india_rank')
        state_rank_val = request.form.get('state_rank')

        result.score = float(score_val) if score_val and score_val.strip() else None
        result.percentile = float(percentile_val) if percentile_val and percentile_val.strip() else None
        result.all_india_rank = int(air_val) if air_val and air_val.strip() else None
        result.state_rank = int(state_rank_val) if state_rank_val and state_rank_val.strip() else None

        db.session.commit()
        flash("Exam result updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating exam result: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))


# ==========================================
# ADMISSIONS JOURNEY: EDIT COUNSELLING REG
# ==========================================
@app.route('/student/edit_counselling_reg/<int:reg_id>', methods=['POST'])
@login_required
def edit_counselling_reg(reg_id):
    reg = StudentCounsellingRegistration.query.get_or_404(reg_id)
    student_id = reg.student_id

    try:
        reg.counselling_id = request.form.get('counselling_id')
        reg.registration_status = request.form.get('registration_status')
        reg.application_number = request.form.get('application_number')
        reg.login_username = request.form.get('login_username')
        reg.login_password = request.form.get('login_password')
        reg.registered_email = request.form.get('registered_email')
        reg.registered_mobile = request.form.get('registered_mobile')
        reg.form_confirmation_link = request.form.get('form_confirmation_link')

        db.session.commit()
        flash("Counselling registration updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating registration: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))


# Optional: Delete Exam Result Route
@app.route('/student/delete_exam_result/<int:result_id>', methods=['POST'])
@login_required
def delete_exam_result(result_id):
    result = StudentExamResult.query.get_or_404(result_id)
    student_id = result.student_id
    db.session.delete(result)
    db.session.commit()
    flash("Exam result removed.", "success")
    return redirect(url_for('view_student', id=student_id))


# ==========================================
# ADMISSIONS JOURNEY: SAVE ROUND RESULT
# ==========================================
@app.route('/student/<int:student_id>/add_round_result', methods=['POST'])
@login_required
def add_round_result(student_id):
    try:
        result = StudentRoundResult(
            student_id=student_id,
            round_id=request.form.get('round_id'),
            choices_submitted=request.form.get('choices_submitted') == 'yes',
            allotted_institute=request.form.get('allotted_institute'),
            allotted_branch=request.form.get('allotted_branch'),
            allotted_category=request.form.get('allotted_category'),
            post_allotment_action=request.form.get('post_allotment_action'),
            seat_acceptance_fee_paid=request.form.get('seat_acceptance_fee_paid') == 'yes',
            reporting_status=request.form.get('reporting_status')
        )
        db.session.add(result)
        db.session.commit()
        flash("Round result recorded successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving round result: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))

# ==========================================
# ADMISSIONS HUB: MANAGE ROUNDS
# ==========================================
@app.route('/admissions/counselling/<int:counselling_id>/add_round', methods=['POST'])
@login_required
def add_counselling_round(counselling_id):
    try:
        new_round = CounsellingRound(
            counselling_id=counselling_id,
            round_number=request.form.get('round_number'),
            rules=request.form.get('rules'),
            seat_matrix_link=request.form.get('seat_matrix_link'),
            cutoffs_link=request.form.get('cutoffs_link'),
            result_link=request.form.get('result_link')
        )
        db.session.add(new_round)
        db.session.commit()
        flash(f"Round '{new_round.round_number}' added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding round: {str(e)}", "error")

    return redirect(url_for('admissions_hub'))


@app.route('/admissions/delete_round/<int:round_id>', methods=['POST'])
@login_required
def delete_counselling_round(round_id):
    c_round = CounsellingRound.query.get_or_404(round_id)
    try:
        db.session.delete(c_round)
        db.session.commit()
        flash("Round removed successfully.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("⚠️ Cannot delete this round because students already have seat allotments saved under it.", "error")
    return redirect(url_for('admissions_hub'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)