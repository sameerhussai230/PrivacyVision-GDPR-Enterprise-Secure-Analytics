import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import time
import os
import warnings
from datetime import datetime

# Silence Warnings
os.environ["STREAMLIT_CLIENT_SHOW_ERROR_DETAILS"] = "false"
warnings.filterwarnings("ignore")

DB_CONFIG = {
    "dbname": "smart_city_db",
    "user": "admin",
    "password": "password123",
    "host": "127.0.0.1",
    "port": "5435" 
}

st.set_page_config(page_title="PrivacyVision Analytics", layout="wide")

def init_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_data():
    try:
        conn = init_connection()
        query = "SELECT * FROM footfall_logs ORDER BY timestamp DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except: return pd.DataFrame()

# Sidebar
with st.sidebar:
    st.title("⚙️ Filter")
    if 'selected_date' not in st.session_state:
        st.session_state['selected_date'] = datetime.now().date()
    selected_date = st.date_input("📅 Select Date", st.session_state['selected_date'])
    st.info(f"Viewing: **{selected_date}**")

# Main
st.title("👁️ PrivacyVision: Smart Retail Analytics")
st.markdown("**Status:** 🟢 Live")

df = get_data()

if not df.empty:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date_only'] = df['timestamp'].dt.date
    df_view = df[df['date_only'] == selected_date]
else:
    df_view = pd.DataFrame()

if df_view.empty:
    total_entries, total_exits = 0, 0
else:
    total_entries = len(df_view[df_view['event_type'] == 'ENTRY'])
    total_exits = len(df_view[df_view['event_type'] == 'EXIT'])

col1, col2 = st.columns(2)
col1.metric("Total Entries", total_entries, delta="In")
col2.metric("Total Exits", total_exits, delta="Out")

st.markdown("---")

if not df_view.empty:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📈 Hourly Trend")
        df_view['time_hour'] = df_view['timestamp'].dt.floor('h')
        timeline = df_view.groupby(['time_hour', 'event_type']).size().reset_index(name='count')
        if not timeline.empty:
            fig = px.bar(timeline, x='time_hour', y='count', color='event_type', barmode='group')
            st.plotly_chart(fig, use_container_width=True, key="traffic_chart")
    with c2:
        st.subheader("📋 Log")
        display_cols = df_view[['timestamp', 'event_type', 'tracker_id']].head(10)
        display_cols['timestamp'] = display_cols['timestamp'].dt.strftime('%H:%M:%S')
        st.dataframe(display_cols, use_container_width=True, hide_index=True)

time.sleep(1)
st.rerun()