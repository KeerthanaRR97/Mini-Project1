import streamlit as st
import pandas as pd
import sqlite3
import os

# --- App Header ---
with st.container():
    st.title("🙏 WELCOME!!!")
    st.title("🍽️ LOCAL FOOD WASTE MANAGEMENT SYSTEM 🌍")
    image_path = 'D:/Guvi_Project1/dataset/Images/supwproject-210603134356-thumbnail.jpg'
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.warning("Image not found at the specified path.")
    st.write("Connecting Food Providers with Receivers to Reduce Waste and Feed Communities")

# --- Database Connection ---
DB_PATH = 'D:/Guvi_Project1/env/Scripts/Local_food_WM.db'
if not os.path.exists(DB_PATH):
    st.error("Database file not found. Check DB path.")
    st.stop()

conn = sqlite3.connect(DB_PATH)

# --- Table selection ---
table_options = {
    "Providers": "providers",
    "Receivers": "receivers",
    "Food Listings": "food_listings",
    "Claim Status": "claims"
}
selected_table_name = st.selectbox("📋 Select a Dataset to View", list(table_options.keys()))
table = table_options[selected_table_name]

st.markdown(f"### 🧾 Displaying: {selected_table_name} Details")

# --- Sidebar Filters ---
st.sidebar.header("🔎 Apply Filters")

# Providers
if selected_table_name == "Providers":
    df = pd.read_sql("SELECT * FROM providers", conn)
    df.columns = df.columns.str.strip()
    if all(col in df.columns for col in ["Provider_ID", "City", "Type"]):
        provider_ids =  sorted(int(x) for x in df["Provider_ID"].dropna().unique())
        cities = df["City"].dropna().unique().tolist()
        types = df["Type"].dropna().unique().tolist()

        provider_id = st.sidebar.selectbox("Provider ID", ["All"] + provider_ids)
        city = st.sidebar.selectbox("City", ["All"] + cities)
        provider_type = st.sidebar.selectbox("Provider Type", ["All"] + types)

        if provider_id != "All":
            df = df[df["Provider_ID"] == provider_id]
        if city != "All":
            df = df[df["City"] == city]
        if provider_type != "All":
            df = df[df["Type"] == provider_type]
    else:
        st.warning("Some expected columns are missing in Providers table.")

# Receivers
elif selected_table_name == "Receivers":
    df = pd.read_sql("SELECT * FROM receivers", conn)
    df.columns = df.columns.str.strip()
    if all(col in df.columns for col in ["Receiver_ID", "City", "Type"]):
        receiver_ids = df["Receiver_ID"].dropna().unique().tolist()
        cities = df["City"].dropna().unique().tolist()
        receiver_types = df["Type"].dropna().unique().tolist()

        receiver_id = st.sidebar.selectbox("Receiver ID", ["All"] + receiver_ids)
        city = st.sidebar.selectbox("City", ["All"] + cities)
        receiver_type = st.sidebar.selectbox("Receiver Type", ["All"] + receiver_types)

        if receiver_id != "All":
            df = df[df["Receiver_ID"] == receiver_id]
        if city != "All":
            df = df[df["City"] == city]
        if receiver_type != "All":
            df = df[df["Type"] == receiver_type]
    else:
        st.warning("Some expected columns are missing in Receivers table.")

# Food Listings (WITH JOIN for Provider Details)
elif selected_table_name == "Food Listings":
    base_query = """
        SELECT 
            f.Food_ID, f.Food_Type, f.Meal_Type, f.Quantity, f.Location,
            p.Provider_ID, p.Name AS Provider_Name, p.City AS Provider_City, p.Type AS Provider_Type
        FROM food_listings f
        LEFT JOIN providers p ON f.Provider_ID = p.Provider_ID
    """
    df = pd.read_sql(base_query, conn)
    df.columns = df.columns.str.strip()

    food_ids = df["Food_ID"].dropna().unique().tolist()
    cities = df["Location"].dropna().unique().tolist()
    food_types = df["Food_Type"].dropna().unique().tolist()
    meal_types = df["Meal_Type"].dropna().unique().tolist()

    food_id = st.sidebar.selectbox("Food ID", ["All"] + food_ids)
    city = st.sidebar.selectbox("City", ["All"] + cities)
    food_type = st.sidebar.selectbox("Food Type", ["All"] + food_types)
    meal_type = st.sidebar.selectbox("Meal Type", ["All"] + meal_types)

    if food_id != "All":
        df = df[df["Food_ID"] == food_id]
    if city != "All":
        df = df[df["Location"] == city]
    if food_type != "All":
        df = df[df["Food_Type"] == food_type]
    if meal_type != "All":
        df = df[df["Meal_Type"] == meal_type]

# Claim Status (already has JOINs)
elif selected_table_name == "Claim Status":
    claim_ids = pd.read_sql("SELECT DISTINCT Claim_ID FROM claims", conn)["Claim_ID"].tolist()
    statuses = pd.read_sql("SELECT DISTINCT Status FROM claims", conn)["Status"].tolist()

    claim_id = st.sidebar.selectbox("Claim ID", ["All"] + claim_ids)
    claim_status = st.sidebar.selectbox("Claim Status", ["All"] + statuses)

    base_query = """
        SELECT 
            c.Claim_ID, c.Status, c.Timestamp,
            f.Food_ID, f.Food_Type, f.Meal_Type, f.Quantity, f.Location,
            p.Provider_ID, p.Name AS Provider_Name, p.City AS Provider_City, p.Type AS Provider_Type,
            r.Receiver_ID, r.Name AS Receiver_Name, r.City AS Receiver_City, r.Type AS Receiver_Type
        FROM claims c
        LEFT JOIN food_listings f ON c.Food_ID = f.Food_ID
        LEFT JOIN providers p ON f.Provider_ID = p.Provider_ID
        LEFT JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
    """
    filters = []
    params = []

    if claim_id != "All":
        filters.append("c.Claim_ID = ?")
        params.append(claim_id)
    if claim_status != "All":
        filters.append("c.Status = ?")
        params.append(claim_status)

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    df = pd.read_sql(base_query, conn, params=params)

# --- Display Final Filtered Data ---
st.dataframe(df, use_container_width=True)
st.success(f"✅ {len(df)} records found.")
conn.close()
