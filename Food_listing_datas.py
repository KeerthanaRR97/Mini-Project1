import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date

st.header('🍽️🥘 Food Listings')

# Paths
DB_PATH = 'D:/Guvi_Project1/env/Scripts/Local_food_WM.db'
CSV_PATH = 'D:/Guvi_Project1/dataset/Food_listings_data.csv'

# Show existing listings
st.subheader("📋 All Listed Food Items")
if os.path.exists(CSV_PATH):
    food_df = pd.read_csv(CSV_PATH)
else:
    food_df = pd.DataFrame(columns=[
        "Food_ID", "Food_Name", "Quantity", "Expiry_Date",
        "Provider_ID", "Provider_Type", "Location", "Food_Type", "Meal_Type"
    ])
st.dataframe(food_df, use_container_width=True)

# Initialize database
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_listings (
            Food_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Food_Name TEXT,
            Quantity INTEGER,
            Expiry_Date TEXT,
            Provider_ID INTEGER,
            Provider_Type TEXT,
            Location TEXT,
            Food_Type TEXT,
            Meal_Type TEXT
        )
    ''')
    conn.commit()

    # Load from CSV if table is empty
    cursor.execute("SELECT COUNT(*) FROM food_listings")
    count = cursor.fetchone()[0]
    if count == 0 and os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df.to_sql('food_listings', conn, if_exists='append', index=False)
    conn.close()

# Get next auto-increment ID
def get_next_food_id():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='food_listings'")
    row = cursor.fetchone()
    conn.close()
    return (row[0] + 1) if row else 1

# Insert new food listing
def insert_food(name, qty, exp, pid, ptype, loc, ftype, meal):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO food_listings (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, qty, exp, pid, ptype, loc, ftype, meal))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

# Append to CSV
def append_to_csv(new_row):
    if os.path.exists(CSV_PATH):
        new_row.to_csv(CSV_PATH, mode='a', header=False, index=False)
    else:
        new_row.to_csv(CSV_PATH, mode='w', index=False)

# Get latest inserted record
def get_latest_food():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM food_listings ORDER BY Food_ID DESC LIMIT 1", conn)
    conn.close()
    return df

# Update record
def update_food(fid, name, qty, exp, ftype, meal):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE food_listings
        SET Food_Name=?, Quantity=?, Expiry_Date=?, Food_Type=?, Meal_Type=?
        WHERE Food_ID=?
    ''', (name, qty, exp, ftype, meal, fid))
    conn.commit()
    conn.close()

    df = pd.read_csv(CSV_PATH)
    df.loc[df['Food_ID'] == fid, ['Food_Name', 'Quantity', 'Expiry_Date', 'Food_Type', 'Meal_Type']] = [name, qty, exp, ftype, meal]
    df.to_csv(CSV_PATH, index=False)

# Delete record
def delete_food(fid):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food_listings WHERE Food_ID=?", (fid,))
    conn.commit()
    conn.close()

    df = pd.read_csv(CSV_PATH)
    df = df[df['Food_ID'] != fid]
    df.to_csv(CSV_PATH, index=False)

# Initialize database
initialize_db()

# Registration form
st.markdown("<h3 style='text-align: center;'>📝 List Surplus Food</h3>", unsafe_allow_html=True)

# Get provider options from DB
with sqlite3.connect(DB_PATH) as conn:
    providers = pd.read_sql_query("SELECT DISTINCT Provider_ID, Type, City FROM providers", conn)

provider_ids = sorted(providers["Provider_ID"].dropna().astype(int).unique())
provider_id = st.selectbox("Provider ID", provider_ids)

provider_type = providers.loc[providers["Provider_ID"] == provider_id, "Type"].values[0]
location = providers.loc[providers["Provider_ID"] == provider_id, "City"].values[0]

with st.form("listing_form"):
    food_id = get_next_food_id()
    st.text_input("Food ID", value=str(food_id), disabled=True)

    name = st.text_input("Food Name")
    qty = st.number_input("Quantity", min_value=1, step=1)
    exp_date = st.date_input("Expiry Date", min_value=date.today())
    ftype = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
    meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
    submit = st.form_submit_button("List Food")
    st.subheader("Recently Provider Listing The Surplus Food ")
    st.dataframe(get_latest_food(), use_container_width=True)

    if submit:
        if name and qty and exp_date:
            new_id = insert_food(name, qty, exp_date.strftime("%Y-%m-%d"), provider_id, provider_type, location, ftype, meal_type)
            new_row = pd.DataFrame([{
                'Food_ID': new_id,
                'Food_Name': name,
                'Quantity': qty,
                'Expiry_Date': exp_date.strftime("%Y-%m-%d"),
                'Provider_ID': provider_id,
                'Provider_Type': provider_type,
                'Location': location,
                'Food_Type': ftype,
                'Meal_Type': meal_type
            }])
            append_to_csv(new_row)
            st.success(f"✅ Food item listed with ID {new_id}")
            st.balloons()
            st.dataframe(new_row, use_container_width=True)
        else:
            st.error("Please fill in all fields.")

# Update/Delete section
st.markdown("---")
st.markdown("<h3 style='text-align: center;'>✏️ Update or 🗑️ Delete Food Listing</h3>", unsafe_allow_html=True)

food_ids = food_df['Food_ID'].tolist()
selected_id = st.selectbox("Select Food ID", food_ids)

if selected_id:
    selected_row = food_df[food_df['Food_ID'] == selected_id].iloc[0]

    with st.form("update_delete_form"):
        name_upd = st.text_input("Food Name", selected_row['Food_Name'])
        qty_upd = st.number_input("Quantity", value=int(selected_row['Quantity']), step=1)
        exp_upd = st.date_input("Expiry Date", pd.to_datetime(selected_row['Expiry_Date']))
        ftype_upd = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"], index=["Vegetarian", "Non-Vegetarian", "Vegan"].index(selected_row["Food_Type"]))
        meal_upd = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"], index=["Breakfast", "Lunch", "Dinner", "Snacks"].index(selected_row["Meal_Type"]))

        col1, col2 = st.columns(2)
        with col1:
            updated = st.form_submit_button("✏️ Update")
        with col2:
            deleted = st.form_submit_button("🗑️ Delete")

        if updated:
            update_food(selected_id, name_upd, qty_upd, exp_upd.strftime("%Y-%m-%d"), ftype_upd, meal_upd)
            st.success("✅ Food listing updated.")

        if deleted:
            delete_food(selected_id)
            st.warning(f"🗑️ Food listing with ID {selected_id} has been deleted.")
