import streamlit as st
import pandas as pd
import sqlite3
import os

st.header('🚚📦 Providers')

# Paths
DB_PATH = 'D:/Guvi_Project1/env/Scripts/Local_food_WM.db'
CSV_PATH = 'D:/Guvi_Project1/dataset/providers_data.csv'

st.subheader("📋 All Registered Providers Information")
providers_df = pd.read_csv(CSV_PATH)
st.dataframe(providers_df)


# Initialize the database
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            Provider_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Type TEXT,
            Address TEXT,
            City TEXT,
            Contact TEXT UNIQUE
        )
    ''')
    conn.commit()

    # Load from CSV if table is empty
    cursor.execute("SELECT COUNT(*) FROM providers")
    count = cursor.fetchone()[0]
    if count == 0 and os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.to_sql('providers', conn, if_exists='append', index=False)
    conn.close()

# Get next provider ID
def get_next_provider_id():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='providers'")
    row = cursor.fetchone()
    conn.close()
    return (row[0] + 1) if row else 1

# Insert provider into database
def insert_provider(name, ptype, address, city, contact):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO providers (Name, Type, Address, City, Contact)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, ptype, address, city, contact))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

# Update
def update_provider(pid, name, ptype, address, city, contact):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE providers
        SET Name=?, Type=?, Address=?, City=?, Contact=?
        WHERE Provider_ID=?
    ''', (name, ptype, address, city, contact, pid))
    conn.commit()
    conn.close()

    # Update CSV
    df = pd.read_csv(CSV_PATH)
    df.loc[df['Provider_ID'] == pid, ['Name', 'Type', 'Address', 'City', 'Contact']] = [name, ptype, address, city, contact]
    df.to_csv(CSV_PATH, index=False)

# Delete provider
def delete_provider(pid):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM providers WHERE Provider_ID=?", (pid,))
    conn.commit()
    conn.close()

    df = pd.read_csv(CSV_PATH)
    df = df[df['Provider_ID'] != pid]
    df.to_csv(CSV_PATH, index=False)


# Append to CSV
def append_to_csv(provider_id, name, ptype, address, city, contact):
    new_row = pd.DataFrame([{
        'Provider_ID': provider_id,
        'Name': name,
        'Type': ptype,
        'Address': address,
        'City': city,
        'Contact': contact
    }])
    if os.path.exists(CSV_PATH):
        new_row.to_csv(CSV_PATH, mode='a', header=False, index=False)
    else:
        new_row.to_csv(CSV_PATH, mode='w', index=False)

# Get the last registered provider
def get_latest_provider():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM providers ORDER BY Provider_ID DESC LIMIT 1", conn)
    conn.close()
    return df

# Initialize database
initialize_db()

# Streamlit App
st.markdown("<h3 style='text-align: center;'>📝 Provider Registration Form</h3>", unsafe_allow_html=True)


with st.form("registration_form"):
    provider_id = get_next_provider_id()
    st.text_input("Provider ID", value=str(provider_id), disabled=True)

    name = st.text_input("Name")
    ptype = st.selectbox("Provider Type", ["Restaurant", "Catering Service", "Grocery Store", "Supermarket"])
    address = st.text_area("Address")
    city = st.text_input("City")
    contact = st.text_input("Contact (must be unique)")

    submitted = st.form_submit_button("Register")
    st.subheader("Recently Registered Provider")
    st.dataframe(get_latest_provider(), use_container_width=True)

    if submitted:
        if name and contact and address and city:
            try:
                new_id = insert_provider(name, ptype, address, city, contact)
                append_to_csv(new_id, name, ptype, address, city, contact)
                st.success(f"Provider registered with ID {new_id}")
                st.balloons()
                st.subheader("🎉 Just Registered Provider")
                registered_data = pd.DataFrame([{
                    'Provider_ID': new_id,
                    'Name': name,
                    'Type': ptype,
                    'Address': address,
                    'City': city,
                    'Contact': contact
                }])
                st.dataframe(registered_data, use_container_width=True)
                

            except sqlite3.IntegrityError:
                st.error("Contact must be unique. This provider already exists.")
        else:
            st.error("All fields except 'Type' are required.")


st.markdown("---")
st.markdown("<h3 style='text-align: center;'>✏️ Update or 🗑️ Delete Provider</h3>", unsafe_allow_html=True)

provider_ids = providers_df['Provider_ID'].tolist()
selected_id = st.selectbox("Select Provider ID", provider_ids)

if selected_id:
    selected_row = providers_df[providers_df['Provider_ID'] == selected_id].iloc[0]

    with st.form("update_delete_form"):
        name_upd = st.text_input("Name", selected_row['Name'])
        type_upd = st.selectbox("Provider Type", ["Restaurant", "Catering Service", "Grocery Store", "Supermarket"], index=["Restaurant", "Catering Service", "Grocery Store", "Supermarket"].index(selected_row['Type']))
        address_upd = st.text_area("Address", selected_row['Address'])
        city_upd = st.text_input("City", selected_row['City'])
        contact_upd = st.text_input("Contact", selected_row['Contact'])

        col1, col2 = st.columns(2)
        with col1:
            updated= st.form_submit_button("✏️Update")
        with col2:
            deleted = st.form_submit_button("🗑️Delete")

        if updated:
            try:
                update_provider(selected_id, name_upd, type_upd, address_upd, city_upd, contact_upd)
                st.success("✅ Provider information updated successfully!")
            except sqlite3.IntegrityError:
                st.error("🚫 Contact must be unique. Update failed.")

        if deleted:
            delete_provider(selected_id)
            st.warning(f"🗑️ Provider with ID {selected_id} has been deleted.")