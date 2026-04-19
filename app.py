import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Student, Staff, Document
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vidyasaarthi_super_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vidyasaarthi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure Upload Folder for Documents
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Initialize Database and Login Manager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return Staff.query.get(int(user_id))


# ==========================================
# AUTHENTICATION ROUTES
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Staff.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ==========================================
# DASHBOARD & STUDENT MANAGEMENT
# ==========================================
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    students = Student.query.order_by(Student.created_at.desc()).all()
    return render_template('dashboard.html', students=students)


@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        try:
            # 1. Parse all text data from form
            new_student = Student(
                full_name=request.form['full_name'],
                gender=request.form['gender'],
                dob=datetime.strptime(request.form['dob'], '%Y-%m-%d').date(),
                category=request.form['category'],
                aadhaar_no=request.form['aadhaar_no'],
                mobile_number=request.form['mobile_number'],
                email_address=request.form.get('email_address'),
                father_name=request.form['father_name'],
                mother_name=request.form['mother_name'],
                # Add other fields as necessary from the form...
                # (For brevity, core fields are mapped here)
            )
            db.session.add(new_student)
            db.session.flush()  # Get the new_student.id before committing

            # 2. Handle File Uploads
            # 2. Handle File Uploads & Drive Links
            for doc_type in ['photo', '10th_marksheet', '12th_marksheet', 'aadhaar_card']:
                file = request.files.get(doc_type)
                drive_link = request.form.get(f"{doc_type}_url")  # Fetch the Drive link

                # If they uploaded a file OR provided a link, create a Document record
                if file and file.filename != '' or drive_link:
                    file_path_str = ""
                    if file and allowed_file(file.filename):
                        filename = secure_filename(f"{new_student.id}_{doc_type}_{file.filename}")
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        file_path_str = f"uploads/{filename}"

                    new_doc = Document(
                        student_id=new_student.id,
                        doc_type=doc_type,
                        file_path=file_path_str,
                        drive_link=drive_link  # Save the URL to the database
                    )
                    db.session.add(new_doc)

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


@app.route('/student/<int:id>')
@login_required
def view_student(id):
    student = Student.query.get_or_404(id)
    return render_template('profile.html', student=student)


# ==========================================
# PARENT VERIFICATION EXPORT (NEW REQUIREMENT)
# ==========================================
@app.route('/student/<int:id>/export')
@login_required
def export_verification(id):
    """
    Renders a print-optimized, A4 sized page with VidyaSaarthi branding.
    Team can press Ctrl+P to save as PDF and send to parents.
    """
    student = Student.query.get_or_404(id)
    return render_template('verification_sheet.html', student=student)


# ==========================================
# INITIALIZATION COMMANDS
# ==========================================
@app.cli.command("init-db")
def init_db():
    """Run `flask init-db` in terminal to create tables and admin user."""
    db.create_all()
    if not Staff.query.filter_by(username='admin').first():
        admin = Staff(username='admin', password_hash=generate_password_hash('admin123'), role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Database initialized! Default login is admin / admin123")


if __name__ == '__main__':
    app.run(debug=True, port=5000)