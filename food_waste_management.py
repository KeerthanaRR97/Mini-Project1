import streamlit as st
import pandas as pd
import sqlite3


st.set_page_config(page_title="LOCAL FOOD WASTE MANAGEMENT", page_icon=":material/edit:")



home = st.Page("homepage.py", title="Homepage", icon=":material/circle:")
provider = st.Page("Providers.py", title="Providers", icon=":material/circle:")
receiver = st.Page("Receivers.py", title="Receivers", icon=":material/circle:")
food = st.Page("Food_listing_datas.py", title="Food Details", icon=":material/circle:")
status = st.Page("claim_status.py", title="Claim Status", icon=":material/circle:")
query = st.Page("Queries.py", title="Queries", icon=":material/circle:")
about = st.Page("About.py", title="About", icon=":material/circle:")


pg = st.navigation([home, provider,receiver,food,status,query,about])
pg.run()


print('✅ All Done')