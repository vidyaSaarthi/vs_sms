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


MASTER_DOC_TYPES = [
    'photo', 'student_signature', 'aadhaar_card', '10th_marksheet', '11th_marksheet', '12th_marksheet',
    'bank_proof', 'birth_certificate', 'residence_proof', 'caste_certificate', 'ews_certificate',
    'family_id', 'character_certificate', 'improvement_marksheet', 'neet_jee_result', 'passport',
    'school_leaving_certificate', 'transfer_certificate', 'father_aadhaar', 'mother_aadhaar',
    'neet_jee_admit_card', 'student_pan_card', 'apaar_id_doc', 'fingerprints', 'driving_license'
]


@login_manager.user_loader
def load_user(user_id): return Staff.query.get(int(user_id))


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
    if exam_filter in ['NEET', 'JEE']: query = query.filter(Student.exam_type == exam_filter)
    if search_query: query = query.filter(Student.full_name.ilike(f'%{search_query}%'))
    students = query.order_by(Student.created_at.desc()).all()
    return render_template('dashboard.html', students=students, exam_filter=exam_filter, search_query=search_query)


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
                "overall_main": {
                    "max": request.form.get('c10_overall_main_max'), "obt": request.form.get('c10_overall_main_obt'),
                    "perc": request.form.get('c10_overall_main_perc')
                },
                "overall_grand": {
                    "max": request.form.get('c10_overall_grand_max'), "obt": request.form.get('c10_overall_grand_obt'),
                    "perc": request.form.get('c10_overall_grand_perc')
                }
            }

            c12_marks = {
                "main": {
                    "eng": {"max": request.form.get('c12_main_eng_max'), "obt": request.form.get('c12_main_eng_obt')},
                    "phy": {"max": request.form.get('c12_main_phy_max'), "obt": request.form.get('c12_main_phy_obt')},
                    "chem": {"max": request.form.get('c12_main_chem_max'), "obt": request.form.get('c12_main_chem_obt')}
                },
                "other": {"subjects": extract_dynamic_marks('c12', 'other')},
                "additional": {"subjects": extract_dynamic_marks('c12', 'add')},
                "overall_main": {
                    "max": request.form.get('c12_overall_main_max'), "obt": request.form.get('c12_overall_main_obt'),
                    "perc": request.form.get('c12_overall_main_perc')
                },
                "overall_grand": {
                    "max": request.form.get('c12_overall_grand_max'), "obt": request.form.get('c12_overall_grand_obt'),
                    "perc": request.form.get('c12_overall_grand_perc')
                }
            }

            new_student = Student(
                exam_type=request.form.get('exam_type'), forms_filled=forms_filled_str,
                other_forms_filled=request.form.get('other_forms_filled'),
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

                father_name=request.form.get('father_name'), father_aadhaar_no=request.form.get('father_aadhaar_no'),
                father_education=request.form.get('father_education'),
                father_occupation=request.form.get('father_occupation'),
                mother_name=request.form.get('mother_name'), mother_aadhaar_no=request.form.get('mother_aadhaar_no'),
                mother_education=request.form.get('mother_education'),
                mother_occupation=request.form.get('mother_occupation'),

                family_income=request.form.get('family_income'), bank_holder_name=request.form.get('bank_holder_name'),
                bank_name=request.form.get('bank_name'),
                bank_branch=request.form.get('bank_branch'), bank_address=request.form.get('bank_address'),
                bank_account_no=request.form.get('bank_account_no'), bank_ifsc=request.form.get('bank_ifsc'),

                class_10_year=request.form.get('class_10_year') or None,
                class_10_school=request.form.get('class_10_school'), class_10_state=request.form.get('class_10_state'),
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
                class_12_school=request.form.get('class_12_school'), class_12_state=request.form.get('class_12_state'),
                class_12_serial=request.form.get('class_12_serial'),
                class_12_reg_no=request.form.get('class_12_reg_no'),
                class_12_board=request.form.get('class_12_board'), class_12_issue_date=c12_issue_val,
                class_12_roll_no=request.form.get('class_12_roll_no'),
                class_12_marks_data=json.dumps(c12_marks)
            )
            db.session.add(new_student)
            db.session.flush()

            for doc_type in MASTER_DOC_TYPES:
                raw_link = request.form.get(f"{doc_type}_url")
                if raw_link and raw_link.strip():
                    db.session.add(Document(student_id=new_student.id, doc_type=doc_type,
                                            drive_link=convert_to_embed_link(raw_link.strip())))

            # MULTIPLE CUSTOM DOCUMENTS LOGIC
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
                "overall_main": {
                    "max": request.form.get('c10_overall_main_max'), "obt": request.form.get('c10_overall_main_obt'),
                    "perc": request.form.get('c10_overall_main_perc')
                },
                "overall_grand": {
                    "max": request.form.get('c10_overall_grand_max'), "obt": request.form.get('c10_overall_grand_obt'),
                    "perc": request.form.get('c10_overall_grand_perc')
                }
            }

            c12_marks = {
                "main": {
                    "eng": {"max": request.form.get('c12_main_eng_max'), "obt": request.form.get('c12_main_eng_obt')},
                    "phy": {"max": request.form.get('c12_main_phy_max'), "obt": request.form.get('c12_main_phy_obt')},
                    "chem": {"max": request.form.get('c12_main_chem_max'), "obt": request.form.get('c12_main_chem_obt')}
                },
                "other": {"subjects": extract_dynamic_marks('c12', 'other')},
                "additional": {"subjects": extract_dynamic_marks('c12', 'add')},
                "overall_main": {
                    "max": request.form.get('c12_overall_main_max'), "obt": request.form.get('c12_overall_main_obt'),
                    "perc": request.form.get('c12_overall_main_perc')
                },
                "overall_grand": {
                    "max": request.form.get('c12_overall_grand_max'), "obt": request.form.get('c12_overall_grand_obt'),
                    "perc": request.form.get('c12_overall_grand_perc')
                }
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
            student.father_aadhaar_no = request.form.get('father_aadhaar_no')
            student.father_education = request.form.get('father_education')
            student.father_occupation = request.form.get('father_occupation')

            student.mother_name = request.form.get('mother_name')
            student.mother_aadhaar_no = request.form.get('mother_aadhaar_no')
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
            student.class_12_state = request.form.get('class_12_state')
            student.class_12_serial = request.form.get('class_12_serial')
            student.class_12_reg_no = request.form.get('class_12_reg_no')
            student.class_12_board = request.form.get('class_12_board')
            student.class_12_issue_date = datetime.strptime(request.form.get('class_12_issue_date'),
                                                            '%Y-%m-%d').date() if request.form.get(
                'class_12_issue_date') else None
            student.class_12_roll_no = request.form.get('class_12_roll_no')
            student.class_12_marks_data = json.dumps(c12_marks)

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

            # MULTIPLE CUSTOM DOCUMENTS UPDATE LOGIC
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

        except IntegrityError:
            db.session.rollback()
            flash("Error: That Aadhaar or Mobile Number is already used by another student.")
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
    return render_template('profile.html', student=student)


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)