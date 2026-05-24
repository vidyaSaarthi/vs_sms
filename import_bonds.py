import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db, State, Course, StateBond  # Import models

# 1. Database Connection String
DATABASE_URL = "postgresql://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@shuttle.proxy.rlwy.net:59162/railway"

# 2. Setup standalone engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

EXCEL_FILE_NAME = 'Bond list 2025.xlsx'


def run_import():
    print(f"Reading {EXCEL_FILE_NAME}...")

    try:
        df = pd.read_excel(EXCEL_FILE_NAME)
        df = df.fillna('')
        records = df.to_dict('records')
    except Exception as e:
        print(f"❌ Failed to read Excel file: {e}")
        return

    count = 0
    for row in records:
        state_name = str(row.get('State', '')).strip()
        course_name = str(row.get('Course', '')).strip()
        college_type = str(row.get('College Type', '')).strip()
        service_bond = str(row.get('Service Bond', '')).strip()
        disc_bond = str(row.get('Discontinuation Bond', '')).strip()

        if not state_name and not course_name and not college_type:
            continue

        # 1. Map or Create State (using session)
        state_obj = None
        if state_name:
            state_obj = session.query(State).filter(State.name.ilike(state_name)).first()
            if not state_obj:
                state_obj = State(name=state_name)
                session.add(state_obj)
                session.flush()

        # 2. Map or Create Course
        course_obj = None
        if course_name:
            course_obj = session.query(Course).filter(Course.name.ilike(course_name)).first()
            if not course_obj:
                course_obj = Course(name=course_name)
                session.add(course_obj)
                session.flush()

        # 3. Create or Update the Bond Record
        existing_bond = session.query(StateBond).filter_by(
            state_id=state_obj.id if state_obj else None,
            course_id=course_obj.id if course_obj else None,
            college_type=college_type
        ).first()

        if existing_bond:
            existing_bond.service_bond = service_bond
            existing_bond.discontinuation_bond = disc_bond
        else:
            new_bond = StateBond(
                state_id=state_obj.id if state_obj else None,
                course_id=course_obj.id if course_obj else None,
                college_type=college_type,
                service_bond=service_bond,
                discontinuation_bond=disc_bond
            )
            session.add(new_bond)

        count += 1
        print(f"Processed: {state_name} | {course_name} | {college_type}")

    # Commit all changes
    try:
        session.commit()
        print(f"\n✅ SUCCESS! {count} bond records imported.")
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    run_import()