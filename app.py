import os
import re
import json
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Student, Staff, Document
from sqlalchemy.exc import IntegrityError
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vidyasaarthi_super_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vidyasaarthi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==========================================
# 🛑 MASTER ADMIN PIN
# ==========================================
app.config['ADMIN_PIN'] = '8888'

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def convert_to_embed_link(url):
    if not url: return None
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if not match: match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match: return f"https://drive.google.com/file/d/{match.group(1)}/preview"
    return url


@login_manager.user_loader
def load_user(user_id):
    return Staff.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Staff.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    exam_filter = request.args.get('exam_type', '')
    search_query = request.args.get('search', '').strip()

    query = Student.query
    if exam_filter in ['NEET', 'JEE']:
        query = query.filter(Student.exam_type == exam_filter)
    if search_query:
        query = query.filter(Student.full_name.ilike(f'%{search_query}%'))

    students = query.order_by(Student.created_at.desc()).all()
    return render_template('dashboard.html', students=students, exam_filter=exam_filter, search_query=search_query)


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

            c10_marks = {
                "main_total": request.form.get('c10_total_main'), "grand_total": request.form.get('c10_total_grand'),
                "main_perc": request.form.get('c10_perc_main'), "grand_perc": request.form.get('c10_perc_grand'),
                "eng": {"max": request.form.get('c10_eng_max'), "obt": request.form.get('c10_eng_obt')},
                "hin": {"max": request.form.get('c10_hin_max'), "obt": request.form.get('c10_hin_obt')},
                "math": {"max": request.form.get('c10_math_max'), "obt": request.form.get('c10_math_obt')},
                "sci": {"max": request.form.get('c10_sci_max'), "obt": request.form.get('c10_sci_obt')},
                "sst": {"max": request.form.get('c10_sst_max'), "obt": request.form.get('c10_sst_obt')},
                "comp": {"max": request.form.get('c10_comp_max'), "obt": request.form.get('c10_comp_obt')},
                "add1": {"name": request.form.get('c10_add1_name'), "max": request.form.get('c10_add1_max'),
                         "obt": request.form.get('c10_add1_obt')},
                "add2": {"name": request.form.get('c10_add2_name'), "max": request.form.get('c10_add2_max'),
                         "obt": request.form.get('c10_add2_obt')}
            }
            c12_marks = {
                "main_total": request.form.get('c12_total_main'), "grand_total": request.form.get('c12_total_grand'),
                "main_perc": request.form.get('c12_perc_main'), "grand_perc": request.form.get('c12_perc_grand'),
                "eng": {"max": request.form.get('c12_eng_max'), "obt": request.form.get('c12_eng_obt')},
                "phy": {"max": request.form.get('c12_phy_max'), "obt": request.form.get('c12_phy_obt')},
                "chem": {"max": request.form.get('c12_chem_max'), "obt": request.form.get('c12_chem_obt')},
                "bio": {"max": request.form.get('c12_bio_max'), "obt": request.form.get('c12_bio_obt')},
                "add1": {"name": request.form.get('c12_add1_name'), "max": request.form.get('c12_add1_max'),
                         "obt": request.form.get('c12_add1_obt')},
                "add2": {"name": request.form.get('c12_add2_name'), "max": request.form.get('c12_add2_max'),
                         "obt": request.form.get('c12_add2_obt')}
            }

            new_student = Student(
                exam_type=request.form.get('exam_type'),
                full_name=request.form.get('full_name'), dob=dob_val, gender=request.form.get('gender'),
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

                father_name=request.form.get('father_name'), father_education=request.form.get('father_education'),
                father_occupation=request.form.get('father_occupation'),
                mother_name=request.form.get('mother_name'), mother_education=request.form.get('mother_education'),
                mother_occupation=request.form.get('mother_occupation'),
                family_income=request.form.get('family_income'),

                bank_holder_name=request.form.get('bank_holder_name'), bank_name=request.form.get('bank_name'),
                bank_branch=request.form.get('bank_branch'),
                bank_address=request.form.get('bank_address'), bank_account_no=request.form.get('bank_account_no'),
                bank_ifsc=request.form.get('bank_ifsc'),

                class_10_year=request.form.get('class_10_year') or None,
                class_10_school=request.form.get('class_10_school'),
                class_10_serial=request.form.get('class_10_serial'),
                class_10_reg_no=request.form.get('class_10_reg_no'),
                class_10_board=request.form.get('class_10_board'), class_10_issue_date=c10_issue_val,
                class_10_roll_no=request.form.get('class_10_roll_no'),
                class_10_marks_data=json.dumps(c10_marks),

                class_11_year=request.form.get('class_11_year') or None,
                class_11_school=request.form.get('class_11_school'),
                class_11_roll_no=request.form.get('class_11_roll_no'),

                passed_appearing=request.form.get('passed_appearing'),
                studied_sanskrit=request.form.get('studied_sanskrit'),
                registration_no_apaar_id=request.form.get('registration_no_apaar_id'),
                class_12_year=request.form.get('class_12_year') or None,
                class_12_school=request.form.get('class_12_school'),
                class_12_serial=request.form.get('class_12_serial'),
                class_12_reg_no=request.form.get('class_12_reg_no'),
                class_12_board=request.form.get('class_12_board'), class_12_issue_date=c12_issue_val,
                class_12_roll_no=request.form.get('class_12_roll_no'),
                class_12_marks_data=json.dumps(c12_marks)
            )
            db.session.add(new_student)
            db.session.flush()

            doc_types = ['photo', 'student_signature', 'aadhaar_card', '10th_marksheet', '11th_marksheet',
                         '12th_marksheet', 'bank_proof', 'birth_certificate', 'residence_proof', 'caste_certificate',
                         'ews_certificate', 'family_id', 'character_certificate']
            for doc_type in doc_types:
                raw_link = request.form.get(f"{doc_type}_url")
                if raw_link and raw_link.strip():
                    db.session.add(Document(student_id=new_student.id, doc_type=doc_type,
                                            drive_link=convert_to_embed_link(raw_link.strip())))

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


@app.route('/student/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':

        # 🛑 SECURITY CHECK FOR EDITING
        if student.is_approved:
            provided_pin = request.form.get('admin_pin')
            if provided_pin != app.config['ADMIN_PIN']:
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

            c10_marks = {
                "main_total": request.form.get('c10_total_main'), "grand_total": request.form.get('c10_total_grand'),
                "main_perc": request.form.get('c10_perc_main'), "grand_perc": request.form.get('c10_perc_grand'),
                "eng": {"max": request.form.get('c10_eng_max'), "obt": request.form.get('c10_eng_obt')},
                "hin": {"max": request.form.get('c10_hin_max'), "obt": request.form.get('c10_hin_obt')},
                "math": {"max": request.form.get('c10_math_max'), "obt": request.form.get('c10_math_obt')},
                "sci": {"max": request.form.get('c10_sci_max'), "obt": request.form.get('c10_sci_obt')},
                "sst": {"max": request.form.get('c10_sst_max'), "obt": request.form.get('c10_sst_obt')},
                "comp": {"max": request.form.get('c10_comp_max'), "obt": request.form.get('c10_comp_obt')},
                "add1": {"name": request.form.get('c10_add1_name'), "max": request.form.get('c10_add1_max'),
                         "obt": request.form.get('c10_add1_obt')},
                "add2": {"name": request.form.get('c10_add2_name'), "max": request.form.get('c10_add2_max'),
                         "obt": request.form.get('c10_add2_obt')}
            }
            c12_marks = {
                "main_total": request.form.get('c12_total_main'), "grand_total": request.form.get('c12_total_grand'),
                "main_perc": request.form.get('c12_perc_main'), "grand_perc": request.form.get('c12_perc_grand'),
                "eng": {"max": request.form.get('c12_eng_max'), "obt": request.form.get('c12_eng_obt')},
                "phy": {"max": request.form.get('c12_phy_max'), "obt": request.form.get('c12_phy_obt')},
                "chem": {"max": request.form.get('c12_chem_max'), "obt": request.form.get('c12_chem_obt')},
                "bio": {"max": request.form.get('c12_bio_max'), "obt": request.form.get('c12_bio_obt')},
                "add1": {"name": request.form.get('c12_add1_name'), "max": request.form.get('c12_add1_max'),
                         "obt": request.form.get('c12_add1_obt')},
                "add2": {"name": request.form.get('c12_add2_name'), "max": request.form.get('c12_add2_max'),
                         "obt": request.form.get('c12_add2_obt')}
            }

            student.exam_type = request.form.get('exam_type')
            student.full_name = request.form.get('full_name')
            student.gender = request.form.get('gender')
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
            student.father_education = request.form.get('father_education')
            student.father_occupation = request.form.get('father_occupation')
            student.mother_name = request.form.get('mother_name')
            student.mother_education = request.form.get('mother_education')
            student.mother_occupation = request.form.get('mother_occupation')
            student.family_income = request.form.get('family_income')

            student.bank_holder_name = request.form.get('bank_holder_name')
            student.bank_name = request.form.get('bank_name')
            student.bank_branch = request.form.get('bank_branch')
            student.bank_address = request.form.get('bank_address')
            student.bank_account_no = request.form.get('bank_account_no')
            student.bank_ifsc = request.form.get('bank_ifsc')

            student.class_10_year = request.form.get('class_10_year') or None
            student.class_10_school = request.form.get('class_10_school')
            student.class_10_serial = request.form.get('class_10_serial')
            student.class_10_reg_no = request.form.get('class_10_reg_no')
            student.class_10_board = request.form.get('class_10_board')
            student.class_10_roll_no = request.form.get('class_10_roll_no')
            student.class_10_marks_data = json.dumps(c10_marks)

            student.class_11_year = request.form.get('class_11_year') or None
            student.class_11_school = request.form.get('class_11_school')
            student.class_11_roll_no = request.form.get('class_11_roll_no')

            student.passed_appearing = request.form.get('passed_appearing')
            student.studied_sanskrit = request.form.get('studied_sanskrit')
            student.registration_no_apaar_id = request.form.get('registration_no_apaar_id')
            student.class_12_year = request.form.get('class_12_year') or None
            student.class_12_school = request.form.get('class_12_school')
            student.class_12_serial = request.form.get('class_12_serial')
            student.class_12_reg_no = request.form.get('class_12_reg_no')
            student.class_12_board = request.form.get('class_12_board')
            student.class_12_roll_no = request.form.get('class_12_roll_no')
            student.class_12_marks_data = json.dumps(c12_marks)

            doc_types = ['photo', 'student_signature', 'aadhaar_card', '10th_marksheet', '11th_marksheet',
                         '12th_marksheet', 'bank_proof', 'birth_certificate', 'residence_proof', 'caste_certificate',
                         'ews_certificate', 'family_id', 'character_certificate']
            for doc_type in doc_types:
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

            db.session.commit()
            flash(f"Student {student.full_name} updated successfully!")
            return redirect(url_for('view_student', id=student.id))

        except IntegrityError:
            db.session.rollback()
            flash("Error: That Aadhaar or Mobile Number is already used by another student.")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating student: {str(e)}")

    c10_marks = json.loads(student.class_10_marks_data) if student.class_10_marks_data else {}
    c12_marks = json.loads(student.class_12_marks_data) if student.class_12_marks_data else {}
    docs = {doc.doc_type: doc.drive_link.replace('/preview', '/view') if doc.drive_link else '' for doc in
            student.documents}
    return render_template('edit_student.html', student=student, c10_marks=c10_marks, c12_marks=c12_marks, docs=docs)


@app.route('/student/<int:id>/approve', methods=['POST'])
@login_required
def approve_student(id):
    student = Student.query.get_or_404(id)
    student.is_approved = True
    db.session.commit()
    flash(f"🔒 Security Lock Active! {student.full_name}'s record has been marked as Parent Approved.")
    return redirect(url_for('view_student', id=student.id))


# ==========================================
# NEW: DELETE SECURE ROUTE
# ==========================================
@app.route('/student/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    provided_pin = request.form.get('admin_pin')

    # Security Check
    if provided_pin == app.config['ADMIN_PIN']:
        # Delete related documents first to prevent database orphans
        Document.query.filter_by(student_id=student.id).delete()

        # Delete the actual student record
        student_name = student.full_name
        db.session.delete(student)
        db.session.commit()

        flash(f"🗑️ Record Deleted: {student_name} has been permanently removed from the system.")
        return redirect(url_for('dashboard'))
    else:
        flash("SECURITY BLOCK: Invalid Admin PIN. Deletion cancelled.")
        return redirect(url_for('view_student', id=student.id))


@app.route('/student/<int:id>')
@login_required
def view_student(id):
    student = Student.query.get_or_404(id)
    c10_marks = json.loads(student.class_10_marks_data) if student.class_10_marks_data else {}
    c12_marks = json.loads(student.class_12_marks_data) if student.class_12_marks_data else {}
    return render_template('profile.html', student=student, c10_marks=c10_marks, c12_marks=c12_marks)


@app.route('/student/<int:id>/export')
@login_required
def export_verification(id):
    student = Student.query.get_or_404(id)
    c10_marks = json.loads(student.class_10_marks_data) if student.class_10_marks_data else {}
    c12_marks = json.loads(student.class_12_marks_data) if student.class_12_marks_data else {}
    return render_template('verification_sheet.html', student=student, c10_marks=c10_marks, c12_marks=c12_marks)


@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not Staff.query.filter_by(username='admin').first():
        admin = Staff(username='admin', password_hash=generate_password_hash('admin123'), role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Database initialized! Default login is admin / admin123")


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)