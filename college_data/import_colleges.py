import pandas as pd
import json
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import math

# 🚨 REPLACE THIS with your actual Railway PostgreSQL connection string!
DATABASE_URL = "postgresql://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@shuttle.proxy.rlwy.net:59162/railway"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


def clean_value(val):
    if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
        return None
    if isinstance(val, str):
        v = str(val).strip()
        if v.lower() in ['na', 'nan', '-', 'none', '', 'not mentioned', 'n/a']:
            return None
        return v
    # Force EVERYTHING to be a string before it hits the DB
    return str(val)


print("1. Loading Excel Files...")
location = r'H:\My Drive\Business\Vidya Saarthi\2026\Counsellings\NEET UG\Colleges Study - Perplexity\Haryana_Colleges_Study'
df1 = pd.read_excel('basic_haryana.xlsx')
df2 = pd.read_excel('cutoffs_haryana.xlsx')
df3 = pd.read_excel('College_Database.xlsx')

print("2. Merging Excel 1 and Excel 3...")
merged_df = pd.merge(df1, df3, left_on='college_information_document_name', right_on='document_source_file', how='left')
print(f"   Found {len(merged_df)} unique colleges.")

print("3. Executing Strict Database Import...")
college_id_map = {}
cutoff_count = 0
unmatched_colleges = set()
current_college_processing = "Unknown"

try:
    for index, row in merged_df.iterrows():
        current_college_processing = clean_value(row.get('Cleaned College Name'))
        if not current_college_processing:
            continue

        state_name = clean_value(row.get('State_x')) or clean_value(row.get('state'))
        state_id = None
        if state_name:
            state_result = session.execute(text("SELECT id FROM states WHERE name ILIKE :name"),
                                           {"name": f"%{state_name}%"}).fetchone()
            if state_result: state_id = state_result[0]

        # --- SMART UNIVERSITY LOOKUP ---
        raw_uni_name = clean_value(row.get('University Name')) or clean_value(row.get('University_x')) or clean_value(
            row.get('University'))
        uni_id_val = None
        if raw_uni_name and raw_uni_name.lower() != 'unknown':
            uni_res = session.execute(text("SELECT id FROM universities WHERE name ILIKE :name"),
                                      {"name": raw_uni_name}).fetchone()
            if uni_res:
                uni_id_val = uni_res[0]
            else:
                res = session.execute(text("INSERT INTO universities (name) VALUES (:name) RETURNING id"),
                                      {"name": raw_uni_name})
                uni_id_val = res.fetchone()[0]

        # --- SMART COURSE LOOKUP ---
        raw_course_name = clean_value(row.get('Course_x')) or clean_value(row.get('Course')) or "Unknown"
        course_id_val = None
        if raw_course_name and raw_course_name.lower() != 'unknown':
            course_res = session.execute(text("SELECT id FROM courses WHERE name ILIKE :name"),
                                         {"name": raw_course_name}).fetchone()
            if course_res:
                course_id_val = course_res[0]
            else:
                res = session.execute(text("INSERT INTO courses (name) VALUES (:name) RETURNING id"),
                                      {"name": raw_course_name})
                course_id_val = res.fetchone()[0]

        insert_query = text("""
                    INSERT INTO colleges (
                        name, true_college_name, college_code, college_type, course_id, established_year,
                        state_id, university_id, district, city, complete_address, nearby_airport, nearby_train_station,
                        university_name, state_rank, aiq_rank, fees, service_bond, discontinued_bond,
                        hidden_fees_warning, seat_distribution, overall_rating, academics_rating,
                        clinical_exposure_rating, hostel_mess_rating, campus_life_rating,
                        academics_summary, faculty_mentorship_summary, patient_flow_hospital_summary,
                        hostel_summary, mess_summary, campus_life_summary, pg_prospects_summary,
                        strictness_discipline, gender_rules, top_3_strengths, top_3_red_flags,
                        counselor_one_liner, document_source_file
                    ) VALUES (
                        :name, :true_name, :code, :type, :c_id, :year, :state_id, :uni_id, :district, :city, :address,
                        :airport, :train, :uni, :state_rank, :aiq_rank, :fees, :service, :disc,
                        :hidden, :seats, :orating, :arating, :crating, :hrating, :lrating,
                        :asum, :fsum, :psum, :hossum, :msum, :csum, :pgsum, :strict, :gender,
                        :str, :red, :oneliner, :doc
                    ) RETURNING id
                """)

        params = {
            "name": current_college_processing,
            "true_name": clean_value(row.get('True College Name')),
            "code": clean_value(row.get('College_code')),
            "type": clean_value(row.get('Type_x')) or clean_value(row.get('Type')) or clean_value(
                row.get('college_type')) or "Unknown",
            "c_id": course_id_val,
            "year": clean_value(row.get('Established year')),
            "state_id": state_id,
            "uni_id": uni_id_val,
            "district": clean_value(row.get('District')),
            "city": clean_value(row.get('city')),
            "address": clean_value(row.get('complete_address')),
            "airport": clean_value(row.get('nearby_airport')),
            "train": clean_value(row.get('nearby_train_station')),
            "uni": raw_uni_name,  # Saves the text string so it shows up on the frontend!
            "state_rank": clean_value(row.get('state_rank')),
            "aiq_rank": clean_value(row.get('aiq_rank')),
            "fees": clean_value(row.get('Fees')),
            "service": clean_value(row.get('Service Bond')),
            "disc": clean_value(row.get('Discontinuation Bond')),
            "hidden": clean_value(row.get('hidden_fees_warning')),
            "seats": clean_value(row.get('seat_distribution')),
            "orating": clean_value(row.get('overall_rating')),
            "arating": clean_value(row.get('academics_rating')),
            "crating": clean_value(row.get('clinical_exposure_rating')),
            "hrating": clean_value(row.get('hostel_mess_rating')),
            "lrating": clean_value(row.get('campus_life_rating')),
            "asum": clean_value(row.get('academics_summary')),
            "fsum": clean_value(row.get('faculty_mentorship_summary')),
            "psum": clean_value(row.get('patient_flow_hospital_summary')),
            "hossum": clean_value(row.get('hostel_summary')),
            "msum": clean_value(row.get('mess_summary')),
            "csum": clean_value(row.get('campus_life_summary')),
            "pgsum": clean_value(row.get('pg_prospects_summary')),
            "strict": clean_value(row.get('strictness_discipline')),
            "gender": clean_value(row.get('gender_rules')),
            "str": clean_value(row.get('top_3_strengths')),
            "red": clean_value(row.get('top_3_red_flags')),
            "oneliner": clean_value(row.get('counselor_one_liner')),
            "doc": clean_value(row.get('college_information_document_name'))
        }

        result = session.execute(insert_query, params)
        new_id = result.fetchone()[0]

        if params['true_name']:
            college_id_map[str(params['true_name']).strip().lower()] = new_id

    # --- PHASE 3: CUTOFFS ---
    base_cols = ['State', 'Course', 'Type', 'College Name', 'Allotted Category']
    round_cols = [c for c in df2.columns if c not in base_cols]

    for index, row in df2.iterrows():
        true_name = clean_value(row.get('College Name'))
        if not true_name: continue

        current_college_processing = f"Cutoffs for {true_name}"
        lookup_name = str(true_name).strip().lower()
        college_id = college_id_map.get(lookup_name)

        if not college_id:
            unmatched_colleges.add(true_name)
            continue

        cutoff_data = {}
        for rc in round_cols:
            val = clean_value(row.get(rc))
            if val is not None:
                cutoff_data[rc] = str(val)

        if cutoff_data:
            insert_cutoff_query = text("""
                INSERT INTO college_cutoffs (college_id, allotted_category, cutoff_data)
                VALUES (:cid, :cat, :data)
            """)
            session.execute(insert_cutoff_query, {
                "cid": college_id,
                "cat": clean_value(row.get('Allotted Category')) or "General",
                "data": json.dumps(cutoff_data)
            })
            cutoff_count += 1

    session.commit()
    print("   Colleges inserted successfully!")
    print(f"   Successfully inserted {cutoff_count} cutoff records!")

    if unmatched_colleges:
        print(
            f"\n⚠️ WARNING: {len(unmatched_colleges)} colleges from Excel 2 did NOT match a 'True College Name' in Excel 1.")

    print("\n🎉 FULL BATCH MIGRATION COMPLETE!")

except Exception as e:
    session.rollback()
    print("\n" + "=" * 50)
    print("❌ CRITICAL ERROR TRIGGERED")
    print("=" * 50)
    print(f"Failed while processing: {current_college_processing}")
    print(f"Error Message: {str(e)}")
    print("\n⏪ FULL ROLLBACK EXECUTED. Zero rows were saved to the database.")
    sys.exit(1)