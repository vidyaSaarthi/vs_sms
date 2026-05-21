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
    return str(val)


def sql_val(val):
    if val is None:
        return 'NULL'
    if isinstance(val, (int, float)):
        return str(val)
    # Escape single quotes in strings for raw SQL insertion
    return f"'{str(val).replace(chr(39), chr(39) + chr(39))}'"


def check_mandatory_columns(df, required_columns, file_name):
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"\n❌ CRITICAL ERROR: {file_name} is missing mandatory columns!")
        for col in missing_cols:
            print(f"   - Missing: '{col}'")
        print("\n🛑 ABORTING script. Please fix the Excel headers and try again.")
        sys.exit(1)
    print(f"  ✅ {file_name} passed column validation.")


print("1. Loading Excel Files...")
location = r'H:\My Drive\Business\Vidya Saarthi\2026\Counsellings\NEET UG\Colleges Study - Perplexity\Haryana_Colleges_Study\\'

df1 = pd.read_excel(location + 'basic_haryana.xlsx', sheet_name="Sheet1")
df2 = pd.read_excel(location + 'cutoffs_haryana.xlsx', sheet_name="Sheet1")
df3 = pd.read_excel(location + 'College_Database.xlsx')

print("\n--- 🛡️ MANDATORY COLUMN CHECKS ---")

df1_required = [
    'Counselling', 'State', 'Cleaned College Name', 'college_information_document_name',
    'True College Name', 'Course', 'Type', 'Service Bond', 'Discontinuation Bond',
    'Fees', 'District', 'University Name', 'Established year', 'state_rank', 'aiq_rank', 'College_code'
]
df2_required = [
    'State', 'Course', 'Type', 'College Name', 'Allotted Quota',
    'Allotted Category', 'Round 1', 'Round 2', 'Round 3'
]
df3_required = [
    'document_source_file', 'college_name', 'course_name', 'state', 'city',
    'complete_address', 'college_type', 'seat_distribution', 'overall_rating',
    'academics_rating', 'academics_summary', 'faculty_mentorship_summary',
    'clinical_exposure_rating', 'patient_flow_hospital_summary', 'hostel_mess_rating',
    'hostel_summary', 'mess_summary', 'campus_life_rating', 'campus_life_summary',
    'pg_prospects_summary', 'hidden_fees_warning', 'strictness_discipline',
    'gender_rules', 'nearby_airport', 'nearby_train_station', 'top_3_strengths',
    'top_3_red_flags', 'counselor_one_liner'
]

check_mandatory_columns(df1, df1_required, "basic_haryana.xlsx (df1)")
check_mandatory_columns(df2, df2_required, "cutoffs_haryana.xlsx (df2)")
check_mandatory_columns(df3, df3_required, "College_Database.xlsx (df3)")

print("\n--- 🧹 NORMALIZING & CHECKING STATES ---")

# Standardize State columns to Title Case with no leading/trailing spaces
df1['State'] = df1['State'].apply(lambda x: str(x).strip().title() if pd.notna(x) else x)
df2['State'] = df2['State'].apply(lambda x: str(x).strip().title() if pd.notna(x) else x)
df3['state'] = df3['state'].apply(lambda x: str(x).strip().title() if pd.notna(x) else x)

# Ensure states perfectly align across all three files
df1_states = set(df1['State'].dropna().unique())
df2_states = set(df2['State'].dropna().unique())
df3_states = set(df3['state'].dropna().unique())

if not (df1_states == df2_states == df3_states):
    print("\n❌ CRITICAL ERROR: State names do not perfectly match across all 3 files!")
    print(f"   - df1 states: {df1_states}")
    print(f"   - df2 states: {df2_states}")
    print(f"   - df3 states: {df3_states}")
    print("🛑 ABORTING script. Ensure all state names match exactly.")
    sys.exit(1)
else:
    print(f"  ✅ SUCCESS: State names align perfectly across all files: {df1_states}")

# Drop df3 state so we don't get 'State_x' and 'State_y' after merging
df3 = df3.drop('state', axis=1)

print("\n2. Merging Excel 1 and Excel 3...")
merged_df = pd.merge(df1, df3, left_on='college_information_document_name', right_on='document_source_file', how='left')

print("\n--- 🛠️ PRE-FLIGHT VALIDATION CHECKS ---")

df1_count = len(df1)
merged_count = len(merged_df)
df1_distinct = df1['Cleaned College Name'].nunique()
merged_distinct = merged_df['Cleaned College Name'].nunique()

print(f"Check 1: Merge Integrity")
print(f"  -> df1 rows: {df1_count} | merged rows: {merged_count}")
print(f"  -> df1 distinct colleges: {df1_distinct} | merged distinct colleges: {merged_distinct}")

if df1_count != merged_count:
    print("\n❌ CRITICAL ERROR: Row count changed after merge! You have duplicate document names in Excel 3 (df3).")
    print("🛑 ABORTING script.")
    sys.exit(1)
else:
    print("  ✅ SUCCESS: Merge preserved exact row counts.")

if df1_distinct != merged_distinct:
    print("\n❌ CRITICAL ERROR: Distinct college count changed after merge!")
    print("🛑 ABORTING script.")
    sys.exit(1)
else:
    print("  ✅ SUCCESS: Distinct college names are preserved.")

df1_true_names = set(df1['True College Name'].dropna().astype(str).str.strip().str.lower())
df2_names = set(df2['College Name'].dropna().astype(str).str.strip().str.lower())

in_df2_not_df1 = df2_names - df1_true_names

print(f"\nCheck 2: Cutoff vs Basic Mapping")
if in_df2_not_df1:
    print(f"❌ CRITICAL ERROR: Found {len(in_df2_not_df1)} colleges in df2 (Cutoffs) that DO NOT EXIST in df1 (Basic)!")
    for c in in_df2_not_df1:
        print(f"   - {c}")
    print("\n🛑 ABORTING script to prevent orphan cutoff records in the database.")
    sys.exit(1)
else:
    print("  ✅ SUCCESS: All colleges in df2 perfectly map to df1.")

print("--- END PRE-FLIGHT CHECKS ---\n")

print("3. Executing Strict Database Import...")
college_id_map = {}
cutoff_count = 0
current_college_processing = "Unknown"
rows_skipped = 0

try:
    for index, row in merged_df.iterrows():
        current_college_processing = clean_value(row.get('Cleaned College Name'))
        if not current_college_processing:
            rows_skipped += 1
            print(f"⚠️ Row {index} SKIPPED: Could not find a valid 'Cleaned College Name'.")
            continue

        # STATE LOOKUP
        state_name = row.get('State')
        state_id = None
        if state_name:
            state_id = session.execute(text(
                f"SELECT id FROM states WHERE name ILIKE '%{state_name.replace(chr(39), chr(39) + chr(39))}%'")).scalar()
        else:
            print("ERROR - State name not found in row. Should be caught by validation.")
            sys.exit(1)

        # UNIVERSITY LOOKUP
        raw_uni_name = clean_value(row.get('University Name')) or "Unknown"
        uni_id_val = None
        if raw_uni_name and raw_uni_name.lower() != 'unknown':
            escaped_uni = raw_uni_name.replace(chr(39), chr(39) + chr(39))
            uni_id_val = session.execute(text(f"SELECT id FROM universities WHERE name ILIKE '{escaped_uni}'")).scalar()
            if not uni_id_val:
                uni_id_val = session.execute(
                    text(f"INSERT INTO universities (name) VALUES ('{escaped_uni}') RETURNING id")).scalar()

        # COURSE LOOKUP
        raw_course_name = clean_value(row.get('Course')) or "Unknown"
        course_id_val = None
        if raw_course_name and raw_course_name.lower() != 'unknown':
            escaped_course = raw_course_name.replace(chr(39), chr(39) + chr(39))
            course_id_val = session.execute(
                text(f"SELECT id FROM courses WHERE name ILIKE '{escaped_course}'")).scalar()
            if not course_id_val:
                course_id_val = session.execute(
                    text(f"INSERT INTO courses (name) VALUES ('{escaped_course}') RETURNING id")).scalar()

        # COUNSELLING LOOKUP
        counselling_name = clean_value(row.get('Counselling'))
        counselling_id = None
        if counselling_name:
            escaped_couns = counselling_name.replace(chr(39), chr(39) + chr(39))
            counselling_id = session.execute(
                text(f"SELECT id FROM counselling WHERE name ILIKE '{escaped_couns}'")).scalar()

        # 🚨 1. PACK ALL VARIABLES INTO A DICTIONARY
        college_data = {
            "name": current_college_processing,
            "counselling_id": counselling_id,
            "true_college_name": clean_value(row.get('True College Name')),
            "college_code": clean_value(row.get('College_code')),
            "college_type": clean_value(row.get('Type')) or 'Unknown',
            "course_id": course_id_val,
            "established_year": clean_value(row.get('Established year')),
            "state_id": state_id,
            "university_id": uni_id_val,
            "district": clean_value(row.get('District')),
            "city": clean_value(row.get('city')),
            "complete_address": clean_value(row.get('complete_address')),
            "nearby_airport": clean_value(row.get('nearby_airport')),
            "nearby_train_station": clean_value(row.get('nearby_train_station')),
            "university_name": raw_uni_name,
            "state_rank": clean_value(row.get('state_rank')),
            "aiq_rank": clean_value(row.get('aiq_rank')),
            "fees": clean_value(row.get('Fees')),
            "service_bond": clean_value(row.get('Service Bond')),
            "discontinued_bond": clean_value(row.get('Discontinuation Bond')),
            "hidden_fees_warning": clean_value(row.get('hidden_fees_warning')),
            "seat_distribution": clean_value(row.get('seat_distribution')),
            "overall_rating": clean_value(row.get('overall_rating')),
            "academics_rating": clean_value(row.get('academics_rating')),
            "clinical_exposure_rating": clean_value(row.get('clinical_exposure_rating')),
            "hostel_mess_rating": clean_value(row.get('hostel_mess_rating')),
            "campus_life_rating": clean_value(row.get('campus_life_rating')),
            "academics_summary": clean_value(row.get('academics_summary')),
            "faculty_mentorship_summary": clean_value(row.get('faculty_mentorship_summary')),
            "patient_flow_hospital_summary": clean_value(row.get('patient_flow_hospital_summary')),
            "hostel_summary": clean_value(row.get('hostel_summary')),
            "mess_summary": clean_value(row.get('mess_summary')),
            "campus_life_summary": clean_value(row.get('campus_life_summary')),
            "pg_prospects_summary": clean_value(row.get('pg_prospects_summary')),
            "strictness_discipline": clean_value(row.get('strictness_discipline')),
            "gender_rules": clean_value(row.get('gender_rules')),
            "top_3_strengths": clean_value(row.get('top_3_strengths')),
            "top_3_red_flags": clean_value(row.get('top_3_red_flags')),
            "counselor_one_liner": clean_value(row.get('counselor_one_liner')),
            "document_source_file": clean_value(row.get('college_information_document_name'))
        }

        # 🚨 2. THE X-RAY PRINT
        print(f"\n--- 🔍 VARIABLES FOR: {current_college_processing} ---")
        # print(json.dumps(college_data, indent=4))

        # 🚨 3. EXECUTE SQL QUERY
        columns = ", ".join(college_data.keys())
        values = ", ".join([str(sql_val(v)) for v in college_data.values()])
        raw_sql_query = f"INSERT INTO colleges ({columns}) VALUES ({values}) RETURNING id;"

        result = session.execute(text(raw_sql_query))
        new_id = result.fetchone()[0]

        true_name_val = clean_value(row.get('True College Name'))
        if true_name_val:
            college_id_map[str(true_name_val).strip().lower()] = new_id

    # --- PHASE 3: CUTOFFS ---
    base_cols = ['State', 'Course', 'Type', 'College Name', 'Allotted Quota', 'Allotted Category']
    round_cols = [c for c in df2.columns if c not in base_cols]

    for index, row in df2.iterrows():
        true_name = clean_value(row.get('College Name'))
        if not true_name: continue

        current_college_processing = f"Cutoffs for {true_name}"
        lookup_name = str(true_name).strip().lower()
        college_id = college_id_map.get(lookup_name)

        if not college_id:
            continue

        cutoff_data = {}
        for rc in round_cols:
            val = clean_value(row.get(rc))
            if val is not None:
                cutoff_data[rc] = str(val)

        if cutoff_data:
            cutoff_json = json.dumps(cutoff_data).replace(chr(39), chr(39) + chr(39))

            # Pack allotted quota as well
            quota_val = clean_value(row.get('Allotted Quota')) or 'Not Specified'
            category_val = clean_value(row.get('Allotted Category')) or 'General'

            raw_cutoff_sql = f"""
                INSERT INTO college_cutoffs (college_id, allotted_quota, allotted_category, cutoff_data)
                VALUES ({college_id}, '{quota_val}' , '{category_val}', '{cutoff_json}')
            """
            print(f"\n--- Running Cutoff Insert for: {true_name} ---")
            # print(raw_cutoff_sql.strip())

            session.execute(text(raw_cutoff_sql))
            cutoff_count += 1

    session.commit()
    print("\n   Colleges inserted successfully!")
    print(f"   Successfully inserted {cutoff_count} cutoff records!")
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