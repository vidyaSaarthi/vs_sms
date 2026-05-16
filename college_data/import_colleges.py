import pandas as pd
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import math

# 🚨 REPLACE THIS with your actual Railway PostgreSQL connection string!
# It should look like: "postgresql://postgres:YOUR_PASSWORD@containers-us-west-XX.railway.app:5432/railway"
DATABASE_URL = "postgresql://postgres:IbjWncmCmbGfvXmdHhchGhtCljcqsXXZ@shuttle.proxy.rlwy.net:59162/railway"

# Connect to the database
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


def clean_value(val):
    """Handles NaN/NaT values from Pandas to prevent database crashes."""
    if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
        return None
    if isinstance(val, str) and str(val).strip().lower() in ['na', 'nan', '-', 'none', '']:
        return None
    return val


print("1. Loading Excel Files...")
df1 = pd.read_excel('excel1.xlsx')
df2 = pd.read_excel('excel2.xlsx')
df3 = pd.read_excel('excel3.xlsx')

# ==========================================
# PHASE 1: MERGE EXCEL 1 & EXCEL 3 (The Base Profile)
# ==========================================
print("2. Merging Excel 1 and Excel 3...")
# Merge on the explicit document name link
merged_df = pd.merge(df1, df3,
                     left_on='college_information_document_name',
                     right_on='document_source_file',
                     how='left')

print(f"   Found {len(merged_df)} unique colleges.")

# ==========================================
# PHASE 2: INSERT COLLEGES INTO DATABASE
# ==========================================
print("3. Pushing Colleges to Database...")

# We will keep a dictionary to map "True College Name" to the new Database ID
college_id_map = {}

for index, row in merged_df.iterrows():
    # Only process if we have a valid name
    if not clean_value(row.get('Cleaned College Name')):
        continue

    # Attempt to link State to existing states in your DB
    state_name = clean_value(row.get('State_x')) or clean_value(row.get('state'))
    state_id = None
    if state_name:
        state_result = session.execute(text("SELECT id FROM states WHERE name ILIKE :name"),
                                       {"name": f"%{state_name}%"}).fetchone()
        if state_result:
            state_id = state_result[0]

    # Insert the main College Record
    insert_query = text("""
        INSERT INTO colleges (
            name, true_college_name, college_code, college_type, established_year,
            state_id, district, city, complete_address, nearby_airport, nearby_train_station,
            university_name, state_rank, aiq_rank, fees, service_bond, discontinued_bond,
            hidden_fees_warning, seat_distribution, overall_rating, academics_rating,
            clinical_exposure_rating, hostel_mess_rating, campus_life_rating,
            academics_summary, faculty_mentorship_summary, patient_flow_hospital_summary,
            hostel_summary, mess_summary, campus_life_summary, pg_prospects_summary,
            strictness_discipline, gender_rules, top_3_strengths, top_3_red_flags,
            counselor_one_liner, document_source_file
        ) VALUES (
            :name, :true_name, :code, :type, :year, :state_id, :district, :city, :address,
            :airport, :train, :uni, :state_rank, :aiq_rank, :fees, :service, :disc,
            :hidden, :seats, :orating, :arating, :crating, :hrating, :lrating,
            :asum, :fsum, :psum, :hossum, :msum, :csum, :pgsum, :strict, :gender,
            :str, :red, :oneliner, :doc
        ) RETURNING id
    """)

    params = {
        "name": clean_value(row.get('Cleaned College Name')),
        "true_name": clean_value(row.get('True College Name')),
        "code": clean_value(row.get('College_code')),
        "type": clean_value(row.get('Type_x')) or clean_value(row.get('college_type')),
        "year": clean_value(row.get('Established year')),
        "state_id": state_id,
        "district": clean_value(row.get('District')),
        "city": clean_value(row.get('city')),
        "address": clean_value(row.get('complete_address')),
        "airport": clean_value(row.get('nearby_airport')),
        "train": clean_value(row.get('nearby_train_station')),
        "uni": clean_value(row.get('University Name')),
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

    try:
        result = session.execute(insert_query, params)
        new_id = result.fetchone()[0]
        # Map the True College Name to the new Database ID for the Cutoffs import!
        true_name = params['true_name']
        if true_name:
            college_id_map[str(true_name).strip().lower()] = new_id
    except Exception as e:
        print(f"Error inserting {params['name']}: {e}")

session.commit()
print("   Colleges inserted successfully!")

# ==========================================
# PHASE 3: INSERT CUTOFFS (Excel 2)
# ==========================================
print("4. Processing Cutoffs (Excel 2)...")
cutoff_count = 0
unmatched_colleges = set()

# Identify round columns dynamically (any column that isn't base info)
base_cols = ['State', 'Course', 'Type', 'College Name', 'Allotted Category']
round_cols = [c for c in df2.columns if c not in base_cols]

for index, row in df2.iterrows():
    true_name = clean_value(row.get('College Name'))
    if not true_name: continue

    # Try to find the College ID we just created
    lookup_name = str(true_name).strip().lower()
    college_id = college_id_map.get(lookup_name)

    if not college_id:
        unmatched_colleges.add(true_name)
        continue

    # Build the dynamic JSON object for the rounds
    cutoff_data = {}
    for rc in round_cols:
        val = clean_value(row.get(rc))
        if val is not None:
            cutoff_data[rc] = str(val)

    # Insert the Cutoff Record
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
print(f"   Successfully inserted {cutoff_count} cutoff records!")

if unmatched_colleges:
    print(
        f"\n⚠️ WARNING: {len(unmatched_colleges)} colleges from Excel 2 did NOT match a 'True College Name' in Excel 1.")
    print("Sample of unmatched names:")
    for name in list(unmatched_colleges)[:10]:
        print(f" - {name}")

print("\n🎉 MIGRATION COMPLETE!")