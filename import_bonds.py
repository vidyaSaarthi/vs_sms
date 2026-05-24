import pandas as pd
from app import app, db
from models import State, Course, StateBond

# ==========================================
# CONFIGURATION
# ==========================================
# Put the exact name of your Excel file here
EXCEL_FILE_NAME = 'Bond list 2025.xlsx'


def run_import():
    print(f"Reading {EXCEL_FILE_NAME}...")

    try:
        # Read the Excel file and fill empty cells with empty strings
        df = pd.read_excel(EXCEL_FILE_NAME)
        df = df.fillna('')
        records = df.to_dict('records')
    except Exception as e:
        print(f"❌ Failed to read Excel file: {e}")
        return

    with app.app_context():
        count = 0
        for row in records:
            state_name = str(row.get('State', '')).strip()
            course_name = str(row.get('Course', '')).strip()
            college_type = str(row.get('College Type', '')).strip()
            service_bond = str(row.get('Service Bond', '')).strip()
            disc_bond = str(row.get('Discontinuation Bond', '')).strip()

            # Skip totally empty rows
            if not state_name and not course_name and not college_type:
                continue

            # 1. Map or Create State
            state_obj = None
            if state_name:
                state_obj = State.query.filter(State.name.ilike(state_name)).first()
                if not state_obj:
                    state_obj = State(name=state_name)
                    db.session.add(state_obj)
                    db.session.flush()

            # 2. Map or Create Course
            course_obj = None
            if course_name:
                course_obj = Course.query.filter(Course.name.ilike(course_name)).first()
                if not course_obj:
                    course_obj = Course(name=course_name)
                    db.session.add(course_obj)
                    db.session.flush()

            # 3. Create or Update the Bond Record
            existing_bond = StateBond.query.filter_by(
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
                db.session.add(new_bond)

            count += 1
            print(f"Processed: {state_name} | {course_name} | {college_type}")

        # Commit all changes to the database
        try:
            db.session.commit()
            print(f"\n✅ SUCCESS! {count} bond records imported into the database.")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Database error during commit: {e}")


if __name__ == "__main__":
    run_import()