import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# Paths
DB_PATH = 'D:/Guvi_Project1/env/Scripts/Local_food_WM.db'
CSV_PATH = 'D:/Guvi_Project1/dataset/claims_data.csv'


st.header('📋Claim Status⏳')

clm_sts = pd.read_csv(CSV_PATH )
st.dataframe(clm_sts) 




# Load claims data
if os.path.exists(CSV_PATH):
    claims_df = pd.read_csv(CSV_PATH)
else:
    claims_df = pd.DataFrame(columns=["Claim_ID", "Food_ID", "Receiver_ID", "Status", "Timestamp"])



# Initialize database
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            Claim_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Food_ID INTEGER,
            Receiver_ID INTEGER,
            Status TEXT,
            Timestamp TEXT
        )
    ''')
    conn.commit()
    if cursor.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0 and os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.to_sql('claims', conn, if_exists='append', index=False)
    conn.close()

# Get next Claim ID
def get_next_claim_id():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='claims'")
    row = cursor.fetchone()
    conn.close()
    return (row[0] + 1) if row else 1

# Insert claim into DB
def insert_claim(food_id, receiver_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO claims (Food_ID, Receiver_ID, Status, Timestamp)
        VALUES (?, ?, 'Pending', ?)
    ''', (food_id, receiver_id, timestamp))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id, timestamp

# Completed a claim
def Completed_claim(claim_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE claims SET Status='Completed' WHERE Claim_ID=?", (claim_id,))
    conn.commit()
    conn.close()

    # Also update CSV
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.loc[df['Claim_ID'] == claim_id, 'Status'] = 'Completed'
        df.to_csv(CSV_PATH, index=False)


# Cancel a claim
def cancel_claim(claim_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE claims SET Status='Cancelled' WHERE Claim_ID=?", (claim_id,))
    conn.commit()
    conn.close()

    # Also update CSV
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.loc[df['Claim_ID'] == claim_id, 'Status'] = 'Cancelled'
        df.to_csv(CSV_PATH, index=False)

# Append to CSV
def append_to_csv(new_row):
    if os.path.exists(CSV_PATH):
        new_row.to_csv(CSV_PATH, mode='a', header=False, index=False)
    else:
        new_row.to_csv(CSV_PATH, mode='w', index=False)

# Get latest claim
def get_latest_claim():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM claims ORDER BY Claim_ID DESC LIMIT 1", conn)
    conn.close()
    return df

# Initialize DB
initialize_db()

# Get available Food_IDs and Receiver_IDs
with sqlite3.connect(DB_PATH) as conn:
    food_ids = pd.read_sql_query("SELECT Food_ID FROM food_listings", conn)['Food_ID'].tolist()
    receiver_ids = pd.read_sql_query("SELECT Receiver_ID FROM receivers", conn)['Receiver_ID'].tolist()

# Claim Form
st.markdown("<h3 style='text-align: center;'>📝 Claim Food</h3>", unsafe_allow_html=True)

with st.form("claim_form"):
    claim_id = get_next_claim_id()
    st.text_input("Claim ID", value=str(claim_id), disabled=True)
    selected_food_id = st.selectbox("Food ID", food_ids)
    selected_receiver_id = st.selectbox("Receiver ID", receiver_ids)
    submit = st.form_submit_button("📥 Submit Claim")

    if submit:
        new_id, timestamp = insert_claim(selected_food_id, selected_receiver_id)
        new_row = pd.DataFrame([{
            "Claim_ID": new_id,
            "Food_ID": selected_food_id,
            "Receiver_ID": selected_receiver_id,
            "Status": "Pending",
            "Timestamp": timestamp
        }])
        append_to_csv(new_row)
        st.success(f"✅ Claim submitted with ID {new_id}")
        st.dataframe(new_row, use_container_width=True)

# Recently submitted claim
st.subheader("📝 Recently Submitted Claim")
st.dataframe(get_latest_claim(), use_container_width=True)

st.markdown("---")

# Complete and Cancel claim section
st.markdown("<h3 style='text-align: center;'>✅ Complete Claim or ❌ Cancel a Claim</h3>", unsafe_allow_html=True)

pending_claims = clm_sts[clm_sts['Status'] == 'Pending']

if not pending_claims.empty:
    selected_claim_id = st.selectbox("Select a Pending Claim ID", pending_claims['Claim_ID'].tolist(), key="action_select")
    
    col1, col2 = st.columns(2)
    with col1:
        Complete = st.button("✅ Complete Claim", key="complete_button")
    with col2:
        Cancel = st.button("❌ Cancel Claim", key="cancel_button")

    if Complete:
        Completed_claim(selected_claim_id)
        st.success(f"✅ Claim ID {selected_claim_id} has been marked as Completed.")

    if Cancel:
        cancel_claim(selected_claim_id)
        st.warning(f"⚠️ Claim ID {selected_claim_id} has been Cancelled.")
else:
    st.info("No pending claims available to cancel.")






