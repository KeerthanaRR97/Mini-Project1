import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title("📊 Food Waste Management - Queries")

# Connect to DB
DB_PATH = 'D:\Guvi_Project1\env\Scripts\Local_food_WM.db'
conn = sqlite3.connect(DB_PATH)

# -------------------------------
# Query Map with Descriptions
# -------------------------------
query_map = {
    # --- Providers & Receivers ---
    "1. How many food providers and receivers are there in each city?": """
        SELECT 
            p.City,
            COUNT(DISTINCT p.Provider_ID) AS Providers,
            COUNT(DISTINCT r.Receiver_ID) AS Receivers
        FROM providers p
        LEFT JOIN receivers r ON p.City = r.City
        GROUP BY p.City
    """,

    "2. Which type of food provider contributes the most food?": """
        SELECT Provider_Type, COUNT(*) AS Total_Food_Items
        FROM food_listings
        GROUP BY Provider_Type
        ORDER BY Total_Food_Items DESC
        LIMIT 1
    """,

    "3. What is the contact information of food providers in a specific city?": """
        SELECT Name, Type, Address, Contact
        FROM providers
        WHERE City = ?
    """,

    "4. Which receivers have claimed the most food?": """
        SELECT r.Name, COUNT(c.Claim_ID) AS Claims
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Name
        ORDER BY Claims DESC
        LIMIT 5
    """,

    # --- Food Listings ---
    "5. What is the total quantity of food available from all providers?": """
        SELECT SUM(Quantity) AS Total_Quantity FROM food_listings
    """,

    "6. Which city has the highest number of food listings?": """
        SELECT City, COUNT(*) AS Listings
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY City
        ORDER BY Listings DESC
        LIMIT 1
    """,

    "7. What are the most commonly available food types?": """
        SELECT Food_Type, COUNT(*) AS Count
        FROM food_listings
        GROUP BY Food_Type
        ORDER BY Count DESC
        LIMIT 5
    """,

    # --- Claims & Distribution ---
    "8. How many food claims have been made for each food item?": """
        SELECT f.Food_Name, COUNT(c.Claim_ID) AS Total_Claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Food_Name
        ORDER BY Total_Claims DESC
    """,

    "9. Which provider has had the highest number of successful food claims?": """
        SELECT p.Name, COUNT(*) AS Successful_Claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        WHERE c.Status = 'Completed'
        GROUP BY p.Name
        ORDER BY Successful_Claims DESC
        LIMIT 1
    """,

    "10. What percentage of food claims are completed vs. pending vs. canceled?": """
        SELECT Status,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) AS Percentage
        FROM claims
        GROUP BY Status
    """,

    # --- Insights & Analysis ---
    "11. What is the average quantity of food claimed per receiver?": """
        SELECT r.Name, ROUND(AVG(f.Quantity), 2) AS Avg_Quantity
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Name
        ORDER BY Avg_Quantity DESC
        LIMIT 10
    """,

    "12. Which meal type is claimed the most?": """
        SELECT Meal_Type, COUNT(*) AS Claim_Count
        FROM food_listings f
        JOIN claims c ON f.Food_ID = c.Food_ID
        GROUP BY Meal_Type
        ORDER BY Claim_Count DESC
        LIMIT 1
    """,

    "13. What is the total quantity of food donated by each provider?": """
        SELECT p.Name, SUM(f.Quantity) AS Total_Donated
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name
        ORDER BY Total_Donated DESC
        LIMIT 10""",
        # --- Operational / Time-based ---
    "14. What is the average time between food listing and claim?": """
        SELECT AVG(JULIANDAY(c.Timestamp) - JULIANDAY(f.Expiry_Date)) AS Avg_Days_Before_Expiry
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
    """,

    "15. How many expired food items are still unclaimed?": """
        SELECT COUNT(*) AS Expired_Unclaimed
        FROM food_listings f
        LEFT JOIN claims c ON f.Food_ID = c.Food_ID
        WHERE f.Expiry_Date < DATE('now') AND c.Claim_ID IS NULL
    """,

    "16. What is the average quantity of food provided by each type of provider?": """
        SELECT Provider_Type, ROUND(AVG(Quantity), 2) AS Avg_Quantity
        FROM food_listings
        GROUP BY Provider_Type
    """,

    "17. Which city has the highest amount of unclaimed food?": """
        SELECT p.City, SUM(f.Quantity) AS Unclaimed_Quantity
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        LEFT JOIN claims c ON f.Food_ID = c.Food_ID
        WHERE c.Claim_ID IS NULL
        GROUP BY p.City
        ORDER BY Unclaimed_Quantity DESC
        LIMIT 1
    """,

    "18. List providers who haven't had any claims": """
        SELECT DISTINCT p.Name, p.City
        FROM providers p
        LEFT JOIN food_listings f ON p.Provider_ID = f.Provider_ID
        LEFT JOIN claims c ON f.Food_ID = c.Food_ID
        WHERE c.Claim_ID IS NULL
    """,

    "19. Which food types are expiring soon (next 3 days)?": """
        SELECT Food_Name, Expiry_Date, Quantity
        FROM food_listings
        WHERE DATE(Expiry_Date) <= DATE('now', '+3 days')
        ORDER BY Expiry_Date
    """,

    "20. Monthly trend of food donations": """
        SELECT strftime('%Y-%m', Expiry_Date) AS Month, SUM(Quantity) AS Total_Donated
        FROM food_listings
        GROUP BY Month
        ORDER BY Month DESC
    """,

    "21. Top 5 most donated food items": """
        SELECT Food_Name, SUM(Quantity) AS Total_Quantity
        FROM food_listings
        GROUP BY Food_Name
        ORDER BY Total_Quantity DESC
        LIMIT 5
    """,

    "22. Number of unique receivers per city": """
        SELECT City, COUNT(DISTINCT Receiver_ID) AS Unique_Receivers
        FROM receivers
        GROUP BY City
    """,

    "23. What is the total number of canceled claims per receiver?": """
        SELECT r.Name, COUNT(*) AS Canceled_Claims
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        WHERE c.Status = 'Canceled'
        GROUP BY r.Name
        ORDER BY Canceled_Claims DESC
        LIMIT 5
    """,

    "24. Average food quantity listed per provider per month": """
        SELECT p.Name, strftime('%Y-%m', f.Expiry_Date) AS Month, ROUND(AVG(f.Quantity), 2) AS Avg_Quantity
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name, Month
        ORDER BY Month DESC
    """,

    "25. Which day of the week has the most food donations?": """
        SELECT strftime('%w', Expiry_Date) AS Weekday, COUNT(*) AS Listings
        FROM food_listings
        GROUP BY Weekday
        ORDER BY Listings DESC

    """
}
# -------------------------------
# Dropdown Selection
# -------------------------------
selected_query = st.selectbox("🔍 Select a query:", list(query_map.keys()))

# Get dynamic list of cities for filtering
provider_cities = pd.read_sql("SELECT DISTINCT City FROM providers", conn)['City'].tolist()
receiver_cities = pd.read_sql("SELECT DISTINCT City FROM receivers", conn)['City'].tolist()
all_cities = sorted(set(provider_cities + receiver_cities))




# Special handling for city input (query 3)
if selected_query == "3. What is the contact information of food providers in a specific city?":
     selected_city = st.selectbox("📍 select a city:", all_cities)
     city_input = selected_city

# Execute query
if st.button("Run Query"):
    try:
        query = query_map[selected_query]
        if selected_query == "3. What is the contact information of food providers in a specific city?":
            df = pd.read_sql_query(query, conn, params=(city_input,))
        else:
            df = pd.read_sql_query(query, conn)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error running query: {e}")

st.title("📊 Food Waste Management - Data Analysis & Chart")


# --- 1. Food Wastage by Category and Location ---
st.header("1️⃣ Food Wastage Trends by Category & Location")
query1 = """
    SELECT Food_Type, Location, COUNT(*) as Total_Wasted
    FROM food_listings
    GROUP BY Food_Type, Location
"""
df1 = pd.read_sql(query1, conn)
st.dataframe(df1)


# --- 2. Most Frequent Food Providers and Their Contributions ---
st.header("2️⃣ Top Food Providers by Contributions")
query2 = """
    SELECT p.Name AS Provider_Name, COUNT(f.Food_ID) AS Contributions
    FROM food_listings f
    JOIN providers p ON f.Provider_ID = p.Provider_ID
    GROUP BY p.Name
    ORDER BY Contributions DESC
    LIMIT 10
"""
df2 = pd.read_sql(query2, conn)
st.dataframe(df2)

fig2, ax2 = plt.subplots(figsize=(10, 4))
sns.barplot(data=df2, x='Provider_Name', y='Contributions', ax=ax2)
plt.xticks(rotation=45)
st.pyplot(fig2)

# --- 3. Highest Demand Locations Based on Food Claims ---
st.header("3️⃣ High-Demand Locations by Food Claims")
query3 = """
    SELECT f.Location, COUNT(c.Claim_ID) AS Claim_Count
    FROM claims c
    JOIN food_listings f ON c.Food_ID = f.Food_ID
    GROUP BY f.Location
    ORDER BY Claim_Count DESC
    LIMIT 10
"""
df3 = pd.read_sql(query3, conn)
st.dataframe(df3)

fig3, ax3 = plt.subplots()
sns.barplot(data=df3, x='Location', y='Claim_Count', ax=ax3)
plt.xticks(rotation=45)
st.pyplot(fig3)

# --- 4. Food Wastage Over Time (by Expiry Date) ---
st.header("4️⃣ Wastage Trend Over Time")
query4 = """
    SELECT DATE(Expiry_Date) AS Date, COUNT(*) AS Wasted_Food_Count
    FROM food_listings
    GROUP BY Date
    ORDER BY Date
"""
df4 = pd.read_sql(query4, conn)
st.line_chart(df4.set_index('Date'))

# --- Optional: Download Report ---
st.markdown("### 📥 Download Report")
csv = df1.to_csv(index=False).encode()
st.download_button("Download Report", csv, "wastage_by_category.csv", "text/csv")

conn.close()
