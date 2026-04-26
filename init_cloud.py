from app import app
from models import db, Staff
from werkzeug.security import generate_password_hash

# 1. Paste your Railway Postgres URL here
# CLOUD_URL = "postgresql+pg8000://YOUR_CLOUD_URL_HERE"
CLOUD_URL = "postgresql+pg8000://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@postgres.railway.internal:5432/railway"


app.config['SQLALCHEMY_DATABASE_URI'] = CLOUD_URL


def initialize_cloud():
    with app.app_context():
        print("🌐 Connecting to Cloud Database...")

        # This command creates all the missing tables (staff, students, documents)
        db.create_all()
        print("✅ Database tables successfully built in the cloud!")

        # Check if admin exists, if not, create it
        if not Staff.query.filter_by(username='admin').first():
            new_admin = Staff(username='admin', password_hash=generate_password_hash('admin123'), role='admin')
            db.session.add(new_admin)
            db.session.commit()
            print("✅ Master Admin account created! (Login: admin / admin123)")
        else:
            print("✅ Master Admin account already exists.")


if __name__ == '__main__':
    initialize_cloud()