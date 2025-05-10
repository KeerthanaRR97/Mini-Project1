import streamlit as st
import pandas as pd
import sqlite3
import os

st.header('🍽️ Receivers ❤️🙏')

# Paths
DB_PATH = 'D:/Guvi_Project1/env/Scripts/Local_food_WM.db'
CSV_PATH = 'D:/Guvi_Project1/dataset/Receivers_data.csv'

st.subheader("📋 All Registered Receivers Information")
receiver_df = pd.read_csv(CSV_PATH)
st.dataframe(receiver_df)

# Initialize SQLite database and import from CSV
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receivers (
            Receiver_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            Type TEXT,
            City TEXT,
            Contact TEXT UNIQUE
        )
    ''')
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM receivers")
    count = cursor.fetchone()[0]

    if count == 0 and os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.to_sql('receivers', conn, if_exists='append', index=False)

    conn.close()

# Get next receiver ID
def get_next_receiver_id():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='receivers'")
    row = cursor.fetchone()
    conn.close()
    return (row[0] + 1) if row else 1

# Insert a new receiver into DB
def insert_receiver(name, rtype, city, contact):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO receivers (Name, Type, City, Contact)
        VALUES (?, ?, ?, ?)
    ''', (name, rtype, city, contact))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

# Update Receiver
def update_receiver(rid, name, rtype, city, contact):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE receivers
        SET Name=?, Type=?, City=?, Contact=?
        WHERE Receiver_ID=?
    ''', (name, rtype, city, contact, rid))
    conn.commit()
    conn.close()

    df = pd.read_csv(CSV_PATH)
    df.loc[df['Receiver_ID'] == rid, ['Name', 'Type', 'City', 'Contact']] = [name, rtype, city, contact]
    df.to_csv(CSV_PATH, index=False)

# Delete Receiver
def delete_receiver(rid):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM receivers WHERE Receiver_ID=?", (rid,))
    conn.commit()
    conn.close()

    df = pd.read_csv(CSV_PATH)
    df = df[df['Receiver_ID'] != rid]
    df.to_csv(CSV_PATH, index=False)

# Append to CSV file
def append_to_csv(receiver_id, name, rtype, city, contact):
    new_row = pd.DataFrame([{
        'Receiver_ID': receiver_id,
        'Name': name,
        'Type': rtype,
        'City': city,
        'Contact': contact
    }])
    if os.path.exists(CSV_PATH):
        new_row.to_csv(CSV_PATH, mode='a', header=False, index=False)
    else:
        new_row.to_csv(CSV_PATH, mode='w', index=False)

# Get the latest inserted receiver
def get_latest_receiver():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM receivers ORDER BY Receiver_ID DESC LIMIT 1", conn)
    conn.close()
    return df

# Initialize database
initialize_db()

# Streamlit App
st.markdown("<h3 style='text-align: center;'>📝 Receiver Registration Form</h3>", unsafe_allow_html=True)

with st.form("receiver_form"):
    receiver_id = get_next_receiver_id()
    st.text_input("Receiver ID", value=str(receiver_id), disabled=True)

    name = st.text_input("Name")
    rtype = st.selectbox("Receiver Type", ["Individual", "Charity", "NGO", "Shelter"])
    city = st.text_input("City")
    contact = st.text_input("Contact (must be unique)")

    submitted = st.form_submit_button("Register")
    st.subheader("Recently Registered Receiver")
    st.dataframe(get_latest_receiver(), use_container_width=True)


    if submitted:
        if name and city and contact:
            try:
                new_id = insert_receiver(name, rtype, city, contact)
                append_to_csv(new_id, name, rtype, city, contact)
                st.success(f"Receiver registered successfully with ID {new_id}")
                st.balloons()
                st.subheader("🎉 Just Registered Register")
                registered_data = pd.DataFrame([{
                    'Receiver_ID': receiver_id,
                    'Name': name,
                    'Type': rtype,
                    'City': city,
                    'Contact': contact
                }])
                st.dataframe(registered_data, use_container_width=True)

                
                

            except sqlite3.IntegrityError:
                st.error("Contact must be unique. This receiver is already registered.")
        else:
            st.error("All fields except 'Type' are required.")

# -------------------- UPDATE & DELETE --------------------
st.markdown("---")
st.markdown("<h3 style='text-align: center;'>✏️ Update or 🗑️ Delete Receiver</h3>", unsafe_allow_html=True)

receiver_ids = receiver_df['Receiver_ID'].tolist()
selected_id = st.selectbox("Select Receiver ID", receiver_ids)

if selected_id:
    selected_row = receiver_df[receiver_df['Receiver_ID'] == selected_id].iloc[0]

    with st.form("update_delete_form"):
        name_upd = st.text_input("Name", selected_row['Name'])
        type_upd = st.selectbox("Receiver Type", ["Individual", "Charity", "NGO", "Shelter"],
                                index=["Individual", "Charity", "NGO", "Shelter"].index(selected_row['Type']))
        city_upd = st.text_input("City", selected_row['City'])
        contact_upd = st.text_input("Contact", selected_row['Contact'])

        col1, col2 = st.columns(2)
        with col1:
            updated = st.form_submit_button("Update")
        with col2:
            deleted = st.form_submit_button("Delete")

        if updated:
            try:
                update_receiver(selected_id, name_upd, type_upd, city_upd, contact_upd)
                st.success("✅ Receiver updated successfully!")
            except sqlite3.IntegrityError:
                st.error("🚫 Contact must be unique. Update failed.")

        if deleted:
            delete_receiver(selected_id)
            st.warning(f"🗑️ Receiver with ID {selected_id} has been deleted.")


