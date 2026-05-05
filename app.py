import os
import re
import json
from datetime import datetime, date
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

# Consolidated Imports (🚨 FinanceRecord added here)
from models import db, Staff, Student, Document, State, StateCategory, University, UniversityCategory, Exam, \
    Counselling, Form, CounsellingRound, RoundSchedule, College, StudentCounsellingRegistration, StudentRoundResult, \
    Course, StudentExamResult, Task, FormEvent, FinanceRecord, StudentFormSubmission

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
# 🚀 AUTOMATIC CLOUD DATABASE BUILDER & TEAM INJECTION
with app.app_context():
    db.create_all()

    # 1. Inject Master Admin
    if not Staff.query.filter_by(username='admin').first():
        db.session.add(Staff(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
        db.session.commit()
        print("✅ Master Admin account automatically injected!")

    # 2. Inject The VidyaSaarthi Counseling Team
    team_members = ['Shubham', 'Shruti', 'Vivek', 'Krishna', 'Yashpreet']

    for member in team_members:
        if not Staff.query.filter_by(username=member).first():
            # Give everyone a default starting password
            db.session.add(Staff(
                username=member,
                password_hash=generate_password_hash('vs383940'),
                role='counselor'
            ))
            print(f"✅ Counselor account for {member} created!")

    db.session.commit()

# ==========================================
# 🚨 SECURITY: AUTO-LOCK FINANCE PORTAL
# ==========================================
@app.before_request
def check_finance_security():
    """
    If the user navigates away from the finances portal,
    automatically destroy the finance session token.
    """
    # Only run this if the user is actually logged in
    if current_user.is_authenticated:
        # Check if they have the finance token
        if session.get('finance_auth'):
            # If the current page they are requesting does NOT start with '/finances'
            # (and is not serving static assets like CSS/JS)
            if not request.path.startswith('/finances') and not request.path.startswith('/static'):
                session.pop('finance_auth', None)
                print(f"🔒 Finance Portal auto-locked because user navigated to {request.path}")


def convert_to_embed_link(url):
    if not url: return None
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if not match: match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match: return f"https://drive.google.com/file/d/{match.group(1)}/preview"
    return url


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

    if not check_password_hash(current_user.password_hash, current_pw):
        flash("Security Alert: Current password is incorrect.", "error")
        return redirect(request.referrer or url_for('dashboard'))

    if new_pw != confirm_pw:
        flash("Validation Error: New passwords do not match.", "error")
        return redirect(request.referrer or url_for('dashboard'))

    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()

    flash("Password updated successfully! Please log in with your new credentials.", "success")
    return redirect(url_for('logout'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ==========================================
# MASTER DATA HUB
# ==========================================
@app.route('/settings/master')
@login_required
def master_data():
    exams = Exam.query.order_by(Exam.name.asc()).all()
    states = State.query.order_by(State.name.asc()).all()
    universities = University.query.order_by(University.name.asc()).all()
    courses = Course.query.order_by(Course.name.asc()).all()

    counsellings = Counselling.query.order_by(Counselling.name.asc()).all()

    counselling_grouped = {}
    for c in counsellings:
        exam_name = c.exam.name if c.exam else "Independent Processes"
        if exam_name not in counselling_grouped:
            counselling_grouped[exam_name] = []
        counselling_grouped[exam_name].append(c)

    exam_course_mapping = {}
    for exam in exams:
        exam_course_mapping[exam.id] = [{'id': c.id, 'name': c.name} for c in exam.courses]

    return render_template('master_data.html', exams=exams, states=states,
                           universities=universities, courses=courses,
                           counsellings=counsellings,
                           counselling_grouped=counselling_grouped,
                           exam_course_mapping=exam_course_mapping)


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

        if data_type == 'exam':
            exam_date_str = request.form.get('exam_date')
            item.exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date() if exam_date_str else None

            exam_end_date_str = request.form.get('exam_end_date')
            item.exam_end_date = datetime.strptime(exam_end_date_str, '%Y-%m-%d').date() if exam_end_date_str else None

            raw_course_ids = request.form.getlist('course_ids')
            item.courses = []
            if raw_course_ids:
                course_ids = [int(cid) for cid in raw_course_ids if cid.isdigit()]
                mapped_courses = Course.query.filter(Course.id.in_(course_ids)).all()
                item.courses.extend(mapped_courses)

        db.session.commit()
        flash(f"Updated successfully to '{item.name}'!", "success")
    return redirect(url_for('master_data'))


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


@app.route('/settings/master/delete/<data_type>/<int:item_id>', methods=['POST'])
@login_required
def delete_master_data(data_type, item_id):
    if data_type == 'exam':
        item = Exam.query.get_or_404(item_id)
    elif data_type == 'state':
        item = State.query.get_or_404(item_id)
    elif data_type == 'university':
        item = University.query.get_or_404(item_id)
    elif data_type == 'course':
        item = Course.query.get_or_404(item_id)
    else:
        flash('Invalid data type.', 'error')
        return redirect(url_for('master_data'))

    try:
        db.session.delete(item)
        db.session.commit()
        flash(f'{data_type.capitalize()} deleted successfully.', 'success')
    except (IntegrityError, ProgrammingError):
        db.session.rollback()
        flash(
            f'Cannot delete this {data_type.capitalize()} because it is actively linked to students or counselling processes. Please remove those connections first.',
            'error')

    return redirect(url_for('master_data'))


@app.route('/settings/add_exam', methods=['POST'])
@login_required
def add_exam():
    try:
        exam_date_str = request.form.get('exam_date')
        exam_end_date_str = request.form.get('exam_end_date')

        exam_date_val = datetime.strptime(exam_date_str, '%Y-%m-%d').date() if exam_date_str else None
        exam_end_val = datetime.strptime(exam_end_date_str, '%Y-%m-%d').date() if exam_end_date_str else None

        new_exam = Exam(
            name=request.form.get('name'),
            exam_date=exam_date_val,
            exam_end_date=exam_end_val
        )

        raw_course_ids = request.form.getlist('course_ids')
        if raw_course_ids:
            course_ids = [int(cid) for cid in raw_course_ids if cid.isdigit()]
            courses = Course.query.filter(Course.id.in_(course_ids)).all()
            new_exam.courses.extend(courses)

        db.session.add(new_exam)
        db.session.commit()
        flash("Exam added successfully with date and courses!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding exam: {str(e)}", "error")
    return redirect(url_for('master_data'))


# ==========================================
# ADMISSIONS HUB (MASTER DATA)
# ==========================================
@app.route('/admissions')
@login_required
def admissions_hub():
    today = date.today().strftime('%Y-%m-%d')

    all_forms = Form.query.order_by(Form.name.asc()).all()
    exam_forms = [f for f in all_forms if f.form_type == 'Exam']
    counselling_forms_list = [f for f in all_forms if f.form_type == 'Counselling']

    counselling_forms_grouped_raw = {}
    for form in counselling_forms_list:
        exam_name = "Independent / Unlinked Processes"
        if form.counselling_id:
            couns = Counselling.query.get(form.counselling_id)
            if couns and couns.exam_id:
                exam = Exam.query.get(couns.exam_id)
                if exam: exam_name = exam.name

        if exam_name not in counselling_forms_grouped_raw:
            counselling_forms_grouped_raw[exam_name] = []
        counselling_forms_grouped_raw[exam_name].append(form)

    counselling_forms_grouped = {
        k: counselling_forms_grouped_raw[k]
        for k in
        sorted(counselling_forms_grouped_raw.keys(), key=lambda x: (x == "Independent / Unlinked Processes", x))
    }

    all_counsellings = Counselling.query.order_by(Counselling.name.asc()).all()
    counselling_grouped_raw = {}
    for c in all_counsellings:
        exam_name = c.exam.name if c.exam else "Independent / Unlinked Processes"
        if exam_name not in counselling_grouped_raw:
            counselling_grouped_raw[exam_name] = []
        counselling_grouped_raw[exam_name].append(c)

    counselling_grouped = {
        k: counselling_grouped_raw[k]
        for k in sorted(counselling_grouped_raw.keys(), key=lambda x: (x == "Independent / Unlinked Processes", x))
    }

    exams = Exam.query.order_by(Exam.name.asc()).all()
    states = State.query.order_by(State.name.asc()).all()
    universities = University.query.order_by(University.name.asc()).all()
    courses = Course.query.order_by(Course.name.asc()).all()

    exam_course_mapping = {}
    for exam in exams:
        sorted_courses = sorted(exam.courses, key=lambda c: c.name)
        exam_course_mapping[exam.id] = [{'id': c.id, 'name': c.name} for c in sorted_courses]

    return render_template('admissions.html',
                           forms=all_forms,
                           exam_forms=exam_forms,
                           counselling_forms_grouped=counselling_forms_grouped,
                           counsellings=all_counsellings,
                           counselling_grouped=counselling_grouped,
                           exams=exams,
                           states=states,
                           universities=universities,
                           courses=courses,
                           exam_course_mapping=exam_course_mapping,
                           today=today)


@app.route('/admissions/add_counselling', methods=['POST'])
@login_required
def add_counselling():
    name = request.form.get('name')
    counselling_type = request.form.get('counselling_type')
    target_id = request.form.get('target_id')
    exam_id_val = request.form.get('exam_id')

    new_counselling = Counselling(
        name=name,
        counselling_type=counselling_type,
        state_id=target_id if counselling_type == 'State' else None,
        university_id=target_id if counselling_type == 'University' else None,
        exam_id=int(exam_id_val) if exam_id_val else None
    )

    raw_course_ids = request.form.getlist('course_ids')
    if raw_course_ids:
        course_ids = [int(cid) for cid in raw_course_ids if cid.isdigit()]
        courses = Course.query.filter(Course.id.in_(course_ids)).all()
        new_counselling.courses.extend(courses)

    db.session.add(new_counselling)
    db.session.commit()
    flash(f"Counselling process '{name}' created successfully!", "success")
    return redirect(url_for('master_data'))


@app.route('/admissions/edit_counselling/<int:item_id>', methods=['POST'])
@login_required
def edit_counselling(item_id):
    c = Counselling.query.get_or_404(item_id)
    c.name = request.form.get('name')
    c.counselling_type = request.form.get('counselling_type')
    target_id = request.form.get('target_id')
    c.state_id = target_id if c.counselling_type == 'State' else None
    c.university_id = target_id if c.counselling_type == 'University' else None

    exam_id_val = request.form.get('exam_id')
    c.exam_id = int(exam_id_val) if exam_id_val else None

    raw_course_ids = request.form.getlist('course_ids')
    c.courses = []
    if raw_course_ids:
        course_ids = [int(cid) for cid in raw_course_ids if cid.isdigit()]
        mapped_courses = Course.query.filter(Course.id.in_(course_ids)).all()
        c.courses.extend(mapped_courses)

    db.session.commit()
    flash("Counselling process updated successfully!", "success")
    return redirect(url_for('master_data'))


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

    if form_type == 'Exam':
        admit_date_str = request.form.get('admit_card_date')
        admit_card_date = datetime.strptime(admit_date_str, '%Y-%m-%d').date() if admit_date_str else None
        admit_card_link = request.form.get('admit_card_link')
    else:
        admit_card_date = None
        admit_card_link = None

    def safe_float(val):
        return float(val) if val and val.strip() else None

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
        document_link=request.form.get('document_link'),
        prospectus_link=request.form.get('prospectus_link')
    )
    db.session.add(new_form)
    db.session.commit()
    flash(f"Form tracking for '{name}' added successfully!", "success")
    return redirect(url_for('admissions_hub'))


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

        if form.form_type == 'Exam':
            admit_date_str = request.form.get('admit_card_date')
            form.admit_card_date = datetime.strptime(admit_date_str, '%Y-%m-%d').date() if admit_date_str else None
            form.admit_card_link = request.form.get('admit_card_link')
        else:
            form.admit_card_date = None
            form.admit_card_link = None

        def safe_float(val):
            return float(val) if val and val.strip() else None

        form.fee_general = safe_float(request.form.get('fee_general'))
        form.fee_obc = safe_float(request.form.get('fee_obc'))
        form.fee_sc_st = safe_float(request.form.get('fee_sc_st'))
        form.fee_female = safe_float(request.form.get('fee_female'))

        form.document_link = request.form.get('document_link')
        form.prospectus_link = request.form.get('prospectus_link')

        db.session.commit()
        flash("Form details updated!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating form: {str(e)}", "error")

    return redirect(url_for('admissions_hub'))


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
        error_str = str(e).lower()
        if 'forms' in error_str:
            flash(
                "⚠️ Cannot delete: There is a Form/Deadline linked to this process. Please delete or edit the Form first.",
                "error")
        elif 'student_counselling_registrations' in error_str:
            flash("⚠️ Cannot delete: There is still at least one student registered for this process.", "error")
        else:
            flash(f"⚠️ Cannot delete due to database constraint.", "error")
    return redirect(url_for('master_data'))


@app.route('/admissions/delete/form/<int:item_id>', methods=['POST'])
@login_required
def delete_form_record(item_id):
    item = Form.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Form deadline removed.", "success")
    return redirect(url_for('admissions_hub'))


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
    return redirect(url_for('master_data'))


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
    return redirect(url_for('master_data'))


@app.route('/admissions/form/<int:form_id>/add_event', methods=['POST'])
@login_required
def add_form_event(form_id):
    try:
        start_str = request.form.get('start_date')
        end_str = request.form.get('end_date')

        new_event = FormEvent(
            form_id=form_id,
            event_name=request.form.get('event_name'),
            start_date=datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else None,
            end_date=datetime.strptime(end_str, '%Y-%m-%d').date() if end_date_str else None,
            event_link=request.form.get('event_link')
        )
        db.session.add(new_event)
        db.session.commit()
        flash("Event added to form successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding event: {str(e)}", "error")
    return redirect(url_for('admissions_hub'))


@app.route('/admissions/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_form_event(event_id):
    event = FormEvent.query.get_or_404(event_id)
    try:
        db.session.delete(event)
        db.session.commit()
        flash("Event removed.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error removing event.", "error")
    return redirect(url_for('admissions_hub'))


# ==========================================
# DASHBOARD
# ==========================================
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()

    master_exams_sorted = Exam.query.filter(
        (Exam.exam_date >= today) |
        (Exam.exam_end_date >= today) |
        (Exam.exam_date == None)
    ).order_by(Exam.exam_date.asc()).all()

    upcoming_exam_forms = Form.query.options(joinedload(Form.events)).filter(
        Form.form_type == 'Exam',
        or_(Form.end_date >= today, Form.end_date == None)
    ).order_by(Form.end_date.asc()).limit(10).all()

    upcoming_couns_forms = Form.query.options(joinedload(Form.events)).filter(
        Form.form_type == 'Counselling',
        or_(Form.end_date >= today, Form.end_date == None)
    ).order_by(Form.end_date.asc()).all()

    counselling_grouped = {}
    for form in upcoming_couns_forms:
        exam_name = "Independent / Unlinked Processes"
        if form.counselling_id:
            couns = Counselling.query.get(form.counselling_id)
            if couns and couns.exam_id:
                exam = Exam.query.get(couns.exam_id)
                if exam: exam_name = exam.name
        if exam_name not in counselling_grouped:
            counselling_grouped[exam_name] = []
        counselling_grouped[exam_name].append(form)

    counselling_grouped = dict(sorted(counselling_grouped.items()))

    upcoming_activities = FormEvent.query.filter(
        or_(FormEvent.end_date >= today, FormEvent.end_date == None)
    ).order_by(FormEvent.end_date.asc()).all()

    return render_template('dashboard.html',
                           master_exams=master_exams_sorted,
                           upcoming_exam_forms=upcoming_exam_forms,
                           counselling_grouped=counselling_grouped,
                           upcoming_activities=upcoming_activities)


# ==========================================
# STUDENT PIPELINE
# ==========================================
@app.route('/students')
@login_required
def student_pipeline():
    search_query = request.args.get('search', '')
    counsellor_filter = request.args.get('counsellor', '')
    status_filter = request.args.get('status', '')
    counselling_filter = request.args.get('counselling', '')
    exam_id_filter = request.args.get('exam_id', '')
    active_tab = request.args.get('tab', 'all')

    query = Student.query

    if search_query:
        query = query.filter(
            db.or_(
                Student.full_name.ilike(f'%{search_query}%'),
                Student.mobile_number.ilike(f'%{search_query}%'),
                Student.aadhaar_no.ilike(f'%{search_query}%')
            )
        )
    if counsellor_filter: query = query.filter(Student.created_by == counsellor_filter)
    if status_filter: query = query.filter(Student.academic_status == status_filter)
    if counselling_filter:
        query = query.join(StudentCounsellingRegistration).filter(
            StudentCounsellingRegistration.counselling_id == int(counselling_filter))
    if exam_id_filter:
        query = query.join(StudentExamResult).filter(StudentExamResult.exam_id == int(exam_id_filter))

    all_count = query.count()
    jee_count = query.filter(Student.exam_type == 'JEE').count()
    neet_count = query.filter(Student.exam_type == 'NEET').count()

    if active_tab == 'jee':
        query = query.filter(Student.exam_type == 'JEE')
    elif active_tab == 'neet':
        query = query.filter(Student.exam_type == 'NEET')

    counsellors = db.session.query(Student.created_by).distinct().filter(Student.created_by != None).all()
    counsellor_list = sorted([c[0] for c in counsellors if c[0]])
    active_counsellings = Counselling.query.order_by(Counselling.name.asc()).all()
    students = query.order_by(Student.full_name.asc()).distinct().all()

    return render_template('students.html', students=students, search_query=search_query, active_tab=active_tab,
                           counsellor_filter=counsellor_filter, status_filter=status_filter,
                           counselling_filter=counselling_filter, exam_id_filter=exam_id_filter,
                           counsellors=counsellor_list, active_counsellings=active_counsellings,
                           all_count=all_count, jee_count=jee_count, neet_count=neet_count)


def extract_dynamic_marks(prefix, group):
    names = request.form.getlist(f'{prefix}_{group}_name[]')
    maxs = request.form.getlist(f'{prefix}_{group}_max[]')
    obts = request.form.getlist(f'{prefix}_{group}_obt[]')
    return [{"name": n, "max": m, "obt": o} for n, m, o in zip(names, maxs, obts) if n.strip()]


@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        if not request.form.get('created_by'):
            flash("Validation Error: Please select a Counselor Name (Created By).", "error")
            return redirect(url_for('add_student'))

        aadhaar_no = request.form.get('aadhaar_no', '').strip() or None
        mobile_number = request.form.get('mobile_number', '').strip() or None

        if aadhaar_no:
            conflict = Student.query.filter_by(aadhaar_no=aadhaar_no).first()
            if conflict:
                flash(f"Error: Aadhaar '{aadhaar_no}' is already registered to {conflict.full_name}!", "error")
                return redirect(url_for('add_student'))

        if mobile_number:
            conflict = Student.query.filter_by(mobile_number=mobile_number).first()
            if conflict:
                flash(f"Error: Mobile number '{mobile_number}' is already registered to {conflict.full_name}!", "error")
                return redirect(url_for('add_student'))

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
                blood_group=request.form.get('blood_group'), religion=request.form.get('religion'),
                category=request.form.get('category'), identification_mark=request.form.get('identification_mark'),

                aadhaar_no=aadhaar_no,
                mobile_number=mobile_number,

                nationality=request.form.get('nationality'),
                nativity=request.form.get('nativity'),
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
                father_organization=request.form.get('father_organization'),

                mother_name=request.form.get('mother_name'), mother_aadhaar_no=request.form.get('mother_aadhaar_no'),
                mother_education=request.form.get('mother_education'),
                mother_occupation=request.form.get('mother_occupation'),
                mother_designation=request.form.get('mother_designation'),
                mother_organization=request.form.get('mother_organization'),

                family_income=request.form.get('family_income'), bank_holder_name=request.form.get('bank_holder_name'),
                bank_name=request.form.get('bank_name'),
                bank_branch=request.form.get('bank_branch'), bank_address=request.form.get('bank_address'),
                bank_account_no=request.form.get('bank_account_no'), bank_ifsc=request.form.get('bank_ifsc'),

                class_10_year=request.form.get('class_10_year') or None,
                class_10_school=request.form.get('class_10_school'),
                class_10_school_type=request.form.get('class_10_school_type'),
                class_10_state=request.form.get('class_10_state'),
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
                class_12_school_type=request.form.get('class_12_school_type'),
                class_12_school_code=request.form.get('class_12_school_code'),
                class_12_center_code=request.form.get('class_12_center_code'),
                class_12_state=request.form.get('class_12_state'), class_12_serial=request.form.get('class_12_serial'),
                class_12_reg_no=request.form.get('class_12_reg_no'), class_12_board=request.form.get('class_12_board'),
                class_12_issue_date=c12_issue_val, class_12_roll_no=request.form.get('class_12_roll_no'),
                class_12_admit_card_id=request.form.get('class_12_admit_card_id'),
                class_12_marks_data=json.dumps(c12_marks),
                created_by=request.form.get('created_by'),
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
            flash(f"Student {new_student.full_name} added successfully!", "success")
            return redirect(url_for('dashboard'))

        except IntegrityError as e:
            db.session.rollback()
            print(f"INTEGRITY ERROR DETAILS: {str(e.orig)}")
            flash(f"Database Error: {str(e.orig)}", "error")

        except Exception as e:
            db.session.rollback()
            flash(f"Error saving student: {str(e)}", "error")

    staff_members = Staff.query.order_by(Staff.username.asc()).all()
    return render_template('add_student.html', staff_members=staff_members)


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
            student.blood_group = request.form.get('blood_group')
            student.religion = request.form.get('religion')
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
            student.father_designation = request.form.get('father_designation')
            student.father_organization = request.form.get('father_organization')

            student.mother_name = request.form.get('mother_name')
            student.mother_aadhaar_no = request.form.get('mother_aadhaar_no')
            student.mother_education = request.form.get('mother_education')
            student.mother_occupation = request.form.get('mother_occupation')
            student.mother_designation = request.form.get('mother_designation')
            student.mother_organization = request.form.get('mother_organization')

            student.family_income = request.form.get('family_income')
            student.bank_holder_name = request.form.get('bank_holder_name')
            student.bank_name = request.form.get('bank_name')
            student.bank_branch = request.form.get('bank_branch')
            student.bank_address = request.form.get('bank_address')
            student.bank_account_no = request.form.get('bank_account_no')
            student.bank_ifsc = request.form.get('bank_ifsc')

            student.class_10_year = request.form.get('class_10_year') or None
            student.class_10_school = request.form.get('class_10_school')
            student.class_10_school_type = request.form.get('class_10_school_type')
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
            student.class_12_school_type = request.form.get('class_12_school_type')
            student.class_12_school_code = request.form.get('class_12_school_code')
            student.class_12_center_code = request.form.get('class_12_center_code')
            student.class_12_state = request.form.get('class_12_state')
            student.class_12_serial = request.form.get('class_12_serial')
            student.class_12_reg_no = request.form.get('class_12_reg_no')
            student.class_12_board = request.form.get('class_12_board')
            student.class_12_roll_no = request.form.get('class_12_roll_no')
            student.class_12_admit_card_id = request.form.get('class_12_admit_card_id')
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
    active_counsellings = Counselling.query.order_by(Counselling.name.asc()).all()
    exams = Exam.query.order_by(Exam.name.asc()).all()

    # 🚨 NEW: Fetch all forms to populate the specific dropdowns!
    master_forms = Form.query.order_by(Form.name.asc()).all()

    return render_template('profile.html',
                           student=student,
                           active_counsellings=active_counsellings,
                           exams=exams,
                           master_forms=master_forms)


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


# ==========================================
# 1. THE UMBRELLA ROUTE (Modified to be lightweight)
# ==========================================
@app.route('/student/<int:student_id>/register_counselling', methods=['POST'])
@login_required
def register_student_counselling(student_id):
    try:
        counselling_id = int(request.form.get('counselling_id'))

        existing_reg = StudentCounsellingRegistration.query.filter_by(
            student_id=student_id,
            counselling_id=counselling_id
        ).first()

        if existing_reg:
            flash("This student is already registered for this umbrella process!", "error")
            return redirect(url_for('view_student', id=student_id))

        reg_status = request.form.get('registration_status', 'Planned')

        registration = StudentCounsellingRegistration(
            student_id=student_id,
            counselling_id=counselling_id,
            registration_status=reg_status,
            registration_date=date.today()
        )
        db.session.add(registration)
        db.session.commit()
        flash(f"Counselling umbrella marked as {reg_status}!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error registering process: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))


@app.route('/student/delete_counselling_reg/<int:reg_id>', methods=['POST'])
@login_required
def delete_counselling_reg(reg_id):
    reg = StudentCounsellingRegistration.query.get_or_404(reg_id)
    student_id = reg.student_id
    counselling_name = reg.counselling.name

    try:
        associated_rounds = StudentRoundResult.query.join(CounsellingRound).filter(
            StudentRoundResult.student_id == student_id,
            CounsellingRound.counselling_id == reg.counselling_id
        ).all()
        for res in associated_rounds: db.session.delete(res)

        db.session.delete(reg)
        db.session.commit()
        flash(f"Removed {counselling_name} from the student's journey.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing participation: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))


@app.route('/student/edit_counselling_reg/<int:reg_id>', methods=['POST'])
@login_required
def edit_counselling_reg(reg_id):
    reg = StudentCounsellingRegistration.query.get_or_404(reg_id)
    try:
        reg.registration_status = request.form.get('registration_status')
        db.session.commit()
        flash("Umbrella status updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating status: {str(e)}", "error")
    return redirect(url_for('view_student', id=reg.student_id))


@app.route('/student/<int:student_id>/add_exam_result', methods=['POST'])
@login_required
def add_exam_result(student_id):
    try:
        result = StudentExamResult(
            student_id=student_id,
            exam_id=request.form.get('exam_id'),
            application_number=request.form.get('application_number'),
            login_username=request.form.get('login_username'),
            login_password=request.form.get('login_password'),
            registered_email=request.form.get('registered_email'),
            registered_mobile=request.form.get('registered_mobile'),
            form_confirmation_link=request.form.get('form_confirmation_link'),
            score=float(request.form.get('score')) if request.form.get('score') else None,
            percentile=float(request.form.get('percentile')) if request.form.get('percentile') else None,
            all_india_rank=int(request.form.get('all_india_rank')) if request.form.get('all_india_rank') else None,
            state_rank=int(request.form.get('state_rank')) if request.form.get('state_rank') else None
        )
        db.session.add(result)
        db.session.commit()
        flash("Exam Form & Result added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving exam data: {str(e)}", "error")
    return redirect(url_for('view_student', id=student_id))


@app.route('/student/edit_exam_result/<int:result_id>', methods=['POST'])
@login_required
def edit_exam_result(result_id):
    res = StudentExamResult.query.get_or_404(result_id)
    student_id = res.student_id
    try:
        # 1. Update the Exam Scores
        res.exam_id = request.form.get('exam_id')
        res.score = request.form.get('score') or None
        res.percentile = request.form.get('percentile') or None
        res.all_india_rank = request.form.get('all_india_rank') or None
        res.state_rank = request.form.get('state_rank') or None

        # 2. Update the Associated Form Submission & Credentials
        submission_id = request.form.get('submission_id')
        form_id_val = request.form.get('form_id')
        app_no = request.form.get('application_number')
        user = request.form.get('login_username')
        pw = request.form.get('login_password')
        link = request.form.get('form_confirmation_link')

        if submission_id:
            # If a milestone already exists for this exam, update it
            sub = StudentFormSubmission.query.get(submission_id)
            if sub:
                sub.form_id = int(form_id_val) if form_id_val else None
                sub.application_number = app_no
                sub.login_username = user
                sub.login_password = pw
                sub.form_confirmation_link = link
        else:
            # If they didn't have credentials before, but added them now, create the milestone
            if form_id_val or app_no or user or pw or link:
                new_sub = StudentFormSubmission(
                    student_id=student_id,
                    exam_id=res.exam_id,
                    form_id=int(form_id_val) if form_id_val else None,
                    application_number=app_no,
                    login_username=user,
                    login_password=pw,
                    form_confirmation_link=link
                )
                db.session.add(new_sub)

        db.session.commit()
        flash("Exam and form details updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating exam: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))


@app.route('/student/delete_exam_result/<int:result_id>', methods=['POST'])
@login_required
def delete_exam_result(result_id):
    result = StudentExamResult.query.get_or_404(result_id)
    student_id = result.student_id
    db.session.delete(result)
    db.session.commit()
    flash("Exam result removed.", "success")
    return redirect(url_for('view_student', id=student_id))


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


@app.route('/colleges')
@login_required
def college_directory():
    search_query = request.args.get('search', '')
    state_filter = request.args.get('state_id', '')
    course_filter = request.args.get('course_id', '')
    type_filter = request.args.get('type', '')

    query = College.query
    if search_query: query = query.filter(College.name.ilike(f'%{search_query}%'))
    if state_filter: query = query.filter(College.state_id == state_filter)
    if course_filter: query = query.filter(College.course_id == course_filter)
    if type_filter: query = query.filter(College.college_type == type_filter)

    colleges = query.order_by(College.name.asc()).all()

    states = State.query.order_by(State.name.asc()).all()
    universities = University.query.order_by(University.name.asc()).all()
    courses = Course.query.order_by(Course.name.asc()).all()

    return render_template('colleges.html',
                           colleges=colleges, states=states,
                           universities=universities, courses=courses,
                           search_query=search_query, state_filter=state_filter,
                           course_filter=course_filter, type_filter=type_filter)


@app.route('/colleges/add', methods=['POST'])
@login_required
def add_college():
    try:
        course_id_val = request.form.get('course_id')
        new_college = College(
            name=request.form.get('name'),
            college_type=request.form.get('college_type'),
            established_year=request.form.get('established_year'),
            state_id=request.form.get('state_id'),
            university_id=request.form.get('university_id'),
            course_id=int(course_id_val) if course_id_val else None,
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


@app.route('/tasks')
@login_required
def tasks_page():
    today = date.today()
    staff_members = Staff.query.order_by(Staff.username.asc()).all()

    if current_user.role == 'admin':
        pending_tasks = Task.query.filter_by(status='Pending').order_by(Task.end_date.asc()).all()
    else:
        pending_tasks = Task.query.filter_by(assigned_to=current_user.username, status='Pending').order_by(
            Task.end_date.asc()).all()

    all_counsellings = Counselling.query.order_by(Counselling.name.asc()).all()

    upcoming_exam_forms = Form.query.filter(Form.end_date >= today, Form.form_type == 'Exam').order_by(
        Form.end_date.asc()).all()

    return render_template('tasks.html',
                           pending_tasks=pending_tasks,
                           staff_members=staff_members,
                           all_counsellings=all_counsellings,
                           upcoming_exam_forms=upcoming_exam_forms)


@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    try:
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        new_task = Task(
            title=request.form.get('title'),
            description=request.form.get('description'),
            start_date=datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None,
            end_date=datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None,
            assigned_to=request.form.get('assigned_to'),
            assigned_by=current_user.username,
            exam_id=request.form.get('exam_id') or None,
            counselling_id=request.form.get('counselling_id') or None,
            form_id=request.form.get('form_id') or None
        )
        db.session.add(new_task)
        db.session.commit()
        flash(f"Task assigned to {new_task.assigned_to} successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating task: {str(e)}", "error")
    return redirect(url_for('tasks_page'))


@app.route('/student/edit_round_result/<int:result_id>', methods=['POST'])
@login_required
def edit_round_result(result_id):
    result = StudentRoundResult.query.get_or_404(result_id)
    student_id = result.student_id
    try:
        result.round_id = request.form.get('round_id')
        result.allotted_institute = request.form.get('allotted_institute')
        result.post_allotment_action = request.form.get('post_allotment_action')
        db.session.commit()
        flash("Round allotment updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating allotment: {str(e)}", "error")
    return redirect(url_for('view_student', id=student_id))


@app.route('/tasks/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        if current_user.role != 'admin' and current_user.username != task.assigned_by:
            flash("You do not have permission to edit this task.", "error")
            return redirect(url_for('tasks_page'))

        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        task.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        task.assigned_to = request.form.get('assigned_to')

        task.exam_id = request.form.get('exam_id') or None
        task.counselling_id = request.form.get('counselling_id') or None
        task.form_id = request.form.get('form_id') or None

        db.session.commit()
        flash(f"Task '{task.title}' updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating task: {str(e)}", "error")
    return redirect(url_for('tasks_page'))


@app.route('/tasks/update/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    new_status = request.form.get('status')
    if new_status in ['Completed', 'Rejected']:
        task.status = new_status
        db.session.commit()
        flash(f"Task marked as {new_status}!", "success")
    return redirect(url_for('tasks_page'))


@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not Staff.query.filter_by(username='admin').first():
        db.session.add(Staff(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
        db.session.commit()
        print("Database initialized! Default login is admin / admin123")


@app.route('/reports/application-matrix')
@login_required
def application_matrix():
    exam_type = request.args.get('exam_type', 'JEE')

    students = Student.query.filter_by(exam_type=exam_type).order_by(Student.full_name.asc()).all()
    student_ids = [s.id for s in students]

    exam_results = StudentExamResult.query.filter(StudentExamResult.student_id.in_(student_ids)).all()
    active_exam_ids = list(set([r.exam_id for r in exam_results]))
    active_exams = Exam.query.filter(Exam.id.in_(active_exam_ids)).order_by(Exam.name.asc()).all()

    exam_matrix = {s.id: {} for s in students}
    for r in exam_results:
        has_app_no = bool(r.application_number and r.application_number.strip())
        exam_matrix[r.student_id][r.exam_id] = 'Filled' if has_app_no else 'Pending'

    exams_grouped = {}
    for exam in active_exams:
        if not exam.courses:
            exams_grouped.setdefault("General / Untagged", []).append(exam)
        else:
            for course in exam.courses:
                exams_grouped.setdefault(course.name, []).append(exam)
    exams_grouped = dict(sorted(exams_grouped.items()))

    couns_regs = StudentCounsellingRegistration.query.filter(
        StudentCounsellingRegistration.student_id.in_(student_ids)).all()
    active_couns_ids = list(set([r.counselling_id for r in couns_regs]))
    active_counsellings = Counselling.query.filter(Counselling.id.in_(active_couns_ids)).order_by(
        Counselling.name.asc()).all()

    couns_matrix = {s.id: {} for s in students}
    for r in couns_regs:
        has_app_no = bool(r.application_number and r.application_number.strip())
        couns_matrix[r.student_id][r.counselling_id] = 'Filled' if has_app_no else 'Pending'

    couns_grouped = {}
    for c in active_counsellings:
        if not c.courses:
            couns_grouped.setdefault("General / Untagged", []).append(c)
        else:
            for course in c.courses:
                couns_grouped.setdefault(course.name, []).append(c)
    couns_grouped = dict(sorted(couns_grouped.items()))

    return render_template('application_matrix.html',
                           students=students,
                           exams_grouped=exams_grouped,
                           exam_matrix=exam_matrix,
                           couns_grouped=couns_grouped,
                           couns_matrix=couns_matrix,
                           exam_type=exam_type)


@app.route('/reports/form-compliance')
@login_required
def form_compliance():
    today = date.today()

    incomplete_couns = []
    incomplete_exam_regs = []
    missing_exam_results = []

    couns_regs = StudentCounsellingRegistration.query.all()
    for reg in couns_regs:
        fields = [
            ('Status', reg.registration_status),
            ('Link', reg.form_confirmation_link),
            ('App No', reg.application_number),
            ('Username', reg.login_username),
            ('Password', reg.login_password),
            ('Email', reg.registered_email),
            ('Mobile', reg.registered_mobile)
        ]
        missing = [name for name, val in fields if not val or not str(val).strip()]
        if missing:
            incomplete_couns.append({
                'student': reg.student,
                'process_name': reg.counselling.name,
                'missing_fields': missing
            })

    exam_results = StudentExamResult.query.all()
    for res in exam_results:
        reg_fields = [
            ('Link', res.form_confirmation_link),
            ('App No', res.application_number),
            ('Username', res.login_username),
            ('Password', res.login_password),
            ('Email', res.registered_email),
            ('Mobile', res.registered_mobile)
        ]
        reg_missing = [name for name, val in reg_fields if not val or not str(val).strip()]
        if reg_missing:
            incomplete_exam_regs.append({
                'student': res.student,
                'exam_name': res.exam.name,
                'missing_fields': reg_missing
            })

        is_result_empty = (res.score is None and res.percentile is None and
                           res.all_india_rank is None and res.state_rank is None)

        exam_end = res.exam.exam_end_date or res.exam.exam_date

        if is_result_empty and exam_end and exam_end < today:
            missing_exam_results.append({
                'student': res.student,
                'exam_name': res.exam.name
            })

    return render_template('form_compliance.html',
                           incomplete_couns=incomplete_couns,
                           incomplete_exam_regs=incomplete_exam_regs,
                           missing_exam_results=missing_exam_results)


@app.route('/finances')
@login_required
def customer_finances():
    if not session.get('finance_auth'):
        return render_template('finances.html', authenticated=False)

    # 1. Capture which tab the user clicked
    active_tab = request.args.get('tab', 'all')

    # 2. Filter records based on the Student's Exam Type
    query = FinanceRecord.query.join(Student)
    if active_tab == 'jee':
        query = query.filter(Student.exam_type == 'JEE')
    elif active_tab == 'neet':
        query = query.filter(Student.exam_type == 'NEET')

    records = query.order_by(FinanceRecord.date.desc()).all()

    # 3. Calculate badge counts for the tabs
    all_count = FinanceRecord.query.count()
    jee_count = FinanceRecord.query.join(Student).filter(Student.exam_type == 'JEE').count()
    neet_count = FinanceRecord.query.join(Student).filter(Student.exam_type == 'NEET').count()

    students = Student.query.order_by(Student.full_name.asc()).all()
    counsellors = Staff.query.order_by(Staff.username.asc()).all()

    service_types = [
        'NEET Enabler', 'NEET Govt. Only', 'NEET Private Only', 'NEET Complete',
        'Ayush Complete', 'Ayush BAMS Only', 'Ayush BHMS Only', 'BDS Only',
        'IISER', 'NISER', 'IISER + NISER', 'Others'
    ]
    payment_modes = ['Cash', 'UPI', 'Website', 'Debit Card', 'Credit Card']

    return render_template('finances.html',
                           authenticated=True,
                           records=records,
                           students=students,
                           counsellors=counsellors,
                           service_types=service_types,
                           payment_modes=payment_modes,
                           active_tab=active_tab,
                           all_count=all_count,
                           jee_count=jee_count,
                           neet_count=neet_count)

@app.route('/finances/login', methods=['POST'])
@login_required
def finance_login():
    pin = request.form.get('finance_pin')
    if pin == '2468':
        session['finance_auth'] = True
        flash("Finance Portal Unlocked.", "success")
    else:
        flash("Access Denied: Incorrect PIN.", "error")

    return redirect(url_for('customer_finances'))


@app.route('/finances/lock')
@login_required
def finance_lock():
    session.pop('finance_auth', None)
    flash("Finance Portal securely locked.", "info")
    return redirect(url_for('dashboard'))


@app.route('/finances/add', methods=['POST'])
@login_required
def add_finance_record():
    try:
        date_str = request.form.get('date')
        record_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()

        def safe_float(val):
            return float(val) if val and val.strip() else 0.0

        total_fees = safe_float(request.form.get('total_fees'))
        installment_1 = safe_float(request.form.get('installment_1'))
        installment_2 = safe_float(request.form.get('installment_2'))

        new_record = FinanceRecord(
            date=record_date,
            student_id=request.form.get('student_id'),
            service_type=request.form.get('service_type'),
            total_fees=total_fees,
            installment_1=installment_1,
            installment_2=installment_2,
            mode_of_payment=request.form.get('mode_of_payment'),
            beneficiary_name=request.form.get('beneficiary_name'),
            comments=request.form.get('comments')
        )

        new_record.calculate_balance()

        db.session.add(new_record)
        db.session.commit()
        flash("Finance record added successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error saving record: {str(e)}", "error")

    return redirect(url_for('customer_finances'))


@app.route('/finances/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_finance_record(record_id):
    record = FinanceRecord.query.get_or_404(record_id)
    try:
        db.session.delete(record)
        db.session.commit()
        flash("Finance record deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting record: {str(e)}", "error")

    return redirect(url_for('customer_finances'))

@app.route('/admin/migrate-legacy-forms')
@login_required
def migrate_legacy_forms():
    # Only let the admin do this
    if current_user.username != 'admin':
        return "Unauthorized", 403

    migrated_count = 0

    # 1. MIGRATE COUNSELLING DATA
    legacy_couns = StudentCounsellingRegistration.query.all()
    for reg in legacy_couns:
        # If they actually filled out credentials, migrate them
        if reg.application_number or reg.login_username or reg.form_confirmation_link:
            new_sub = StudentFormSubmission(
                student_id=reg.student_id,
                counselling_id=reg.counselling_id,
                form_id=None, # Legacy data has no form_id
                application_number=reg.application_number,
                login_username=reg.login_username,
                login_password=reg.login_password,
                registered_email=reg.registered_email,
                registered_mobile=reg.registered_mobile,
                form_confirmation_link=reg.form_confirmation_link,
                submission_date=reg.registration_date
            )
            db.session.add(new_sub)
            migrated_count += 1

    # 2. MIGRATE EXAM DATA
    legacy_exams = StudentExamResult.query.all()
    for res in legacy_exams:
        if res.application_number or res.login_username or res.form_confirmation_link:
            new_sub = StudentFormSubmission(
                student_id=res.student_id,
                exam_id=res.exam_id,
                form_id=None, # Legacy data has no form_id
                application_number=res.application_number,
                login_username=res.login_username,
                login_password=res.login_password,
                registered_email=res.registered_email,
                registered_mobile=res.registered_mobile,
                form_confirmation_link=res.form_confirmation_link
            )
            db.session.add(new_sub)
            migrated_count += 1

    db.session.commit()
    return f"✅ Migration Complete! Safely transferred {migrated_count} legacy credential records to the new Milestones architecture."


@app.route('/student/log_form_submission', methods=['POST'])
@login_required
def log_form_submission():
    student_id = request.form.get('student_id')

    # It will belong to either a Counselling Umbrella OR an Exam
    counselling_id = request.form.get('counselling_id')
    exam_id = request.form.get('exam_id')

    try:
        new_sub = StudentFormSubmission(
            student_id=student_id,
            counselling_id=int(counselling_id) if counselling_id else None,
            exam_id=int(exam_id) if exam_id else None,
            form_id=request.form.get('form_id') or None,
            application_number=request.form.get('application_number'),
            login_username=request.form.get('login_username'),
            login_password=request.form.get('login_password'),
            registered_email=request.form.get('registered_email'),
            registered_mobile=request.form.get('registered_mobile'),
            form_confirmation_link=request.form.get('form_confirmation_link')
        )
        db.session.add(new_sub)
        db.session.commit()
        flash("Form milestone logged successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error logging form: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))

@app.route('/student/delete_form_submission/<int:sub_id>', methods=['POST'])
@login_required
def delete_form_submission(sub_id):
    sub = StudentFormSubmission.query.get_or_404(sub_id)
    student_id = sub.student_id
    try:
        db.session.delete(sub)
        db.session.commit()
        flash("Form submission removed.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error removing submission.", "error")
    return redirect(url_for('view_student', id=student_id))


@app.route('/student/edit_form_submission/<int:sub_id>', methods=['POST'])
@login_required
def edit_form_submission(sub_id):
    sub = StudentFormSubmission.query.get_or_404(sub_id)
    student_id = sub.student_id

    try:
        form_id_val = request.form.get('form_id')
        sub.form_id = int(form_id_val) if form_id_val else None

        sub.application_number = request.form.get('application_number')
        sub.login_username = request.form.get('login_username')
        sub.login_password = request.form.get('login_password')
        sub.registered_email = request.form.get('registered_email')
        sub.registered_mobile = request.form.get('registered_mobile')
        sub.form_confirmation_link = request.form.get('form_confirmation_link')

        db.session.commit()
        flash("Form submission updated and linked successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating form submission: {str(e)}", "error")

    return redirect(url_for('view_student', id=student_id))


@app.route('/admin/view-legacy-data')
@login_required
def view_legacy_data():
    # Security check
    if current_user.username != 'admin':
        return "Unauthorized", 403

    students = Student.query.order_by(Student.full_name.asc()).all()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Legacy Data Report</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; background-color: #f8f9fa; color: #333; }
            h2 { color: #1a202c; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            th, td { padding: 15px; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; }
            th { background-color: #f1f5f9; text-transform: uppercase; font-size: 0.85rem; color: #475569; }
            tr:hover { background-color: #f8fafc; }
            .has-creds { color: #0f5132; background-color: #d1e7dd; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
            .no-creds { color: #6c757d; font-size: 0.85rem; }
            .creds-box { background: #f8f9fa; border: 1px solid #dee2e6; padding: 8px; margin-top: 5px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; }
            ul { list-style-type: none; padding-left: 0; margin: 0; }
            li { margin-bottom: 15px; border-bottom: 1px dashed #eee; padding-bottom: 10px; }
            li:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        </style>
    </head>
    <body>
        <h2>🗄️ Legacy Database Report (Pre-Migration State)</h2>
        <p>This report reads directly from the old <code>StudentCounsellingRegistration</code> and <code>StudentExamResult</code> tables.</p>

        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Student Name</th>
                    <th style="width: 40%;">Legacy Counselling Data</th>
                    <th style="width: 40%;">Legacy Exam Data</th>
                </tr>
            </thead>
            <tbody>
    """

    for student in students:
        # Only show students who actually have legacy data
        if not student.counselling_registrations and not student.exam_results:
            continue

        couns_html = "<ul>"
        for reg in student.counselling_registrations:
            has_creds = bool(reg.application_number or reg.login_username or reg.form_confirmation_link)
            badge = "<span class='has-creds'>Has Credentials (Migrated)</span>" if has_creds else "<span class='no-creds'>Status Only (No Forms)</span>"

            couns_html += f"<li><strong>{reg.counselling.name}</strong> {badge}"
            if has_creds:
                couns_html += f"<div class='creds-box'>App No: {reg.application_number or '-'}<br>User: {reg.login_username or '-'}<br>Pass: {reg.login_password or '-'}</div>"
            couns_html += "</li>"
        couns_html += "</ul>"

        exam_html = "<ul>"
        for res in student.exam_results:
            has_creds = bool(res.application_number or res.login_username or res.form_confirmation_link)
            badge = "<span class='has-creds'>Has Credentials (Migrated)</span>" if has_creds else "<span class='no-creds'>Scores Only (No Forms)</span>"
            exam_name = res.exam.name if res.exam else "Unknown Exam"

            exam_html += f"<li><strong>{exam_name}</strong> {badge}"
            if has_creds:
                exam_html += f"<div class='creds-box'>App No: {res.application_number or '-'}<br>User: {res.login_username or '-'}<br>Pass: {res.login_password or '-'}</div>"
            exam_html += "</li>"
        exam_html += "</ul>"

        html += f"""
            <tr>
                <td><strong>{student.full_name}</strong></td>
                <td>{couns_html if student.counselling_registrations else "<span style='color:#999'>No Counselling</span>"}</td>
                <td>{exam_html if student.exam_results else "<span style='color:#999'>No Exams</span>"}</td>
            </tr>
        """

    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html


@app.route('/admin/legacy-forms-tracker')
@login_required
def legacy_forms_tracker():
    # Security check
    if current_user.username != 'admin':
        return "Unauthorized", 403

    # Fetch ALL form submissions where the form_id is blank (Legacy)
    unlinked_submissions = StudentFormSubmission.query.filter_by(form_id=None).all()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Legacy Forms Tracker</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; background-color: #f8f9fa; color: #333; }}
            h2 {{ color: #1a202c; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
            .alert-info {{ background-color: #e0f2fe; color: #0369a1; padding: 15px; border-radius: 8px; font-weight: bold; margin-bottom: 20px; border-left: 5px solid #0284c7; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            th, td {{ padding: 15px; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: middle; }}
            th {{ background-color: #f1f5f9; text-transform: uppercase; font-size: 0.85rem; color: #475569; }}
            tr:hover {{ background-color: #f8fafc; }}
            .btn {{ display: inline-block; padding: 8px 15px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-size: 0.85rem; font-weight: bold; }}
            .btn:hover {{ background: #1d4ed8; }}
            .hint-text {{ font-family: monospace; font-size: 0.9rem; color: #64748b; background: #f1f5f9; padding: 4px 8px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h2>🔍 Legacy Forms To-Do List</h2>
        <div class="alert-info">
            There are currently {len(unlinked_submissions)} forms in the database that are displaying as "Legacy Form Submission".
        </div>

        <table>
            <thead>
                <tr>
                    <th>Student Name</th>
                    <th>Journey (Umbrella)</th>
                    <th>Saved Credentials (Hint)</th>
                    <th style="text-align: right;">Action</th>
                </tr>
            </thead>
            <tbody>
    """

    for sub in unlinked_submissions:
        # Check if this legacy form belongs to an Exam or a Counselling process
        journey_name = "Unknown"
        if sub.counselling_id and sub.counselling:
            journey_name = f"📁 Counselling: <strong>{sub.counselling.name}</strong>"
        elif sub.exam_id and sub.exam:
            journey_name = f"📝 Exam: <strong>{sub.exam.name}</strong>"

        # Show a snippet of what credentials it holds, so you know which form to link it to
        hints = []
        if sub.application_number: hints.append(f"App No: {sub.application_number}")
        if sub.login_username: hints.append(f"User: {sub.login_username}")
        hint_str = "<br>".join(hints) if hints else "<em>No App No or Username saved</em>"

        html += f"""
            <tr>
                <td style="font-size: 1.1rem;"><strong>{sub.student.full_name if sub.student else 'Unknown Student'}</strong></td>
                <td>{journey_name}</td>
                <td><span class="hint-text">{hint_str}</span></td>
                <td style="text-align: right;">
                    <a href='/student/{sub.student_id}' target='_blank' class='btn'>Go to Profile →</a>
                </td>
            </tr>
        """

    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html


@app.route('/admin/missing-master-forms-audit')
@login_required
def missing_master_forms_audit():
    # Security check
    if current_user.username != 'admin':
        return "Unauthorized", 403

    # 1. Audit Exams
    all_exams = Exam.query.order_by(Exam.name.asc()).all()
    exams_without_forms = []

    for exam in all_exams:
        # Check if any form in the Forms directory is linked to this exam
        linked_forms_count = Form.query.filter_by(exam_id=exam.id).count()
        if linked_forms_count == 0:
            exams_without_forms.append(exam)

    # 2. Audit Counselling Processes
    all_counsellings = Counselling.query.order_by(Counselling.name.asc()).all()
    couns_without_forms = []

    for couns in all_counsellings:
        # Check if any form in the Forms directory is linked to this counselling process
        linked_forms_count = Form.query.filter_by(counselling_id=couns.id).count()
        if linked_forms_count == 0:
            couns_without_forms.append(couns)

    # 3. Generate the HTML Report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Missing Master Forms Audit</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; background-color: #f8f9fa; color: #333; }}
            .container {{ max-width: 1000px; margin: 0 auto; display: flex; gap: 30px; }}
            .column {{ flex: 1; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            h2 {{ color: #1a202c; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-top: 0; }}
            .badge-count {{ background: #ef4444; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.9rem; margin-left: 10px; }}
            ul {{ list-style-type: none; padding: 0; margin-top: 20px; }}
            li {{ padding: 15px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }}
            li:last-child {{ border-bottom: none; }}
            .btn {{ display: inline-block; padding: 6px 12px; background: #2563eb; color: white; text-decoration: none; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }}
            .btn:hover {{ background: #1d4ed8; }}
            .empty-state {{ text-align: center; color: #10b981; padding: 30px 0; font-weight: bold; }}
            .alert-info {{ background-color: #e0f2fe; color: #0369a1; padding: 15px; border-radius: 8px; font-weight: bold; margin-bottom: 30px; border-left: 5px solid #0284c7; text-align: center; }}
        </style>
    </head>
    <body>
        <div style="max-width: 1000px; margin: 0 auto;">
            <h1 style="color: #1a202c; text-align: center; margin-bottom: 10px;">📋 Forms Directory Audit</h1>
            <div class="alert-info">
                This dashboard identifies master processes that currently have <strong>Zero Master Forms</strong> assigned to them in the Forms Directory.
            </div>
        </div>

        <div class="container">
            <!-- EXAMS COLUMN -->
            <div class="column">
                <h2>📝 Exams <span class="badge-count">{len(exams_without_forms)}</span></h2>
                """

    if exams_without_forms:
        html += "<ul>"
        for e in exams_without_forms:
            html += f"<li><strong>{e.name}</strong> <a href='/admin/manage_forms' target='_blank' class='btn'>Add Form</a></li>"
        html += "</ul>"
    else:
        html += "<div class='empty-state'>✅ All active exams have at least one master form created!</div>"

    html += """
            </div>

            <!-- COUNSELLING COLUMN -->
            <div class="column">
                <h2>📁 Counselling <span class="badge-count">{len(couns_without_forms)}</span></h2>
                """

    if couns_without_forms:
        html += "<ul>"
        for c in couns_without_forms:
            html += f"<li><strong>{c.name}</strong> <a href='/admin/manage_forms' target='_blank' class='btn'>Add Form</a></li>"
        html += "</ul>"
    else:
        html += "<div class='empty-state'>✅ All active counselling processes have at least one master form created!</div>"

    html += """
            </div>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)

