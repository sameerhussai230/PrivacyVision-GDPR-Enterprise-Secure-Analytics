
import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import time
import warnings
import os
from datetime import datetime

# --------------------------------------------------------------------------------
# 0. SYSTEM CONFIGURATION
# --------------------------------------------------------------------------------
os.environ["STREAMLIT_CLIENT_SHOW_ERROR_DETAILS"] = "false"
warnings.filterwarnings("ignore")

# Database Credentials
DB_CONFIG = {
    "dbname": "smart_city_db",
    "user": "admin",
    "password": "password123",
    "host": "127.0.0.1",
    "port": "5435" 
}

st.set_page_config(
    page_title="PrivacyVision Analytics",
    page_icon="👁️",
    layout="wide"
)

# Custom CSS for the live indicator
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 3.5rem; }
    .live-dot { color: #00FF00; font-weight: bold; animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 1. DATABASE HELPERS
# --------------------------------------------------------------------------------
def init_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_data():
    """
    Fetches data and handles Timezone Conversion (Docker UTC -> Local Time)
    """
    try:
        conn = init_connection()
        query = "SELECT * FROM footfall_logs ORDER BY timestamp DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            # 1. Convert to datetime object
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 2. Timezone Correction
            # Docker saves in UTC (Naive). We force it to UTC, then convert to Local System Time.
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            
            # Convert to System Local Time (e.g., Asia/Kolkata)
            df['timestamp'] = df['timestamp'].dt.tz_convert(None) 
            
            # Create a date_only column for filtering
            df['date_only'] = df['timestamp'].dt.date
            
        return df
    except Exception as e:
        # In case of DB connection error, return empty DF
        return pd.DataFrame()

# --------------------------------------------------------------------------------
# 2. DATA LOADING & SIDEBAR
# --------------------------------------------------------------------------------
df = get_data()

with st.sidebar:
    st.title("⚙️ Filter")
    
    # LOGIC FIX: 
    # Default to the LATEST date in the database, not "Today".
    # This ensures data is visible even if DB time (UTC) lags behind Local time.
    if not df.empty:
        default_date = df['date_only'].max()
    else:
        default_date = datetime.now().date()
    
    selected_date = st.date_input(
        "📅 Select Date", 
        value=default_date
    )
    
    st.markdown("---")
    st.info(f"Viewing Data for: **{selected_date}**")
    
    if st.button("🔄 Force Refresh"):
        st.rerun()

# --------------------------------------------------------------------------------
# 3. MAIN DASHBOARD LAYOUT
# --------------------------------------------------------------------------------
st.title("👁️ PrivacyVision-GDPR: Enterprise Secure Analytics")
st.markdown("Status: <span class='live-dot'>●</span> **Live Monitoring**", unsafe_allow_html=True)
st.markdown("---")

# --------------------------------------------------------------------------------
# 4. DATA PROCESSING
# --------------------------------------------------------------------------------

# Filter Logic
if not df.empty:
    df_view = df[df['date_only'] == selected_date]
else:
    df_view = pd.DataFrame()

# --------------------------------------------------------------------------------
# 5. KEY PERFORMANCE INDICATORS (KPIs)
# --------------------------------------------------------------------------------
if df_view.empty:
    if df.empty:
        st.warning("⚠️ Database is empty. Waiting for events...")
    else:
        # Check if data exists for other dates to help user
        available_dates = df['date_only'].unique()
        st.warning(f"No records found for {selected_date}.")
        st.info(f"💡 Data is available for these dates: {available_dates}")
        
    total_entries, total_exits = 0, 0
else:
    total_entries = len(df_view[df_view['event_type'] == 'ENTRY'])
    total_exits = len(df_view[df_view['event_type'] == 'EXIT'])

col1, col2 = st.columns(2)
col1.metric("Total Entries", total_entries, delta="In")
col2.metric("Total Exits", total_exits, delta="Out")

st.markdown("---")

# --------------------------------------------------------------------------------
# 6. CHARTS & LOGS
# --------------------------------------------------------------------------------
if not df_view.empty:
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("📈 Hourly Traffic Trend")
        # Group by Hour
        df_view['time_hour'] = df_view['timestamp'].dt.floor('h')
        timeline = df_view.groupby(['time_hour', 'event_type']).size().reset_index(name='count')
        
        if not timeline.empty:
            fig = px.bar(timeline, x='time_hour', y='count', color='event_type',
                          barmode='group',
                          color_discrete_map={'ENTRY': '#00CC96', 'EXIT': '#EF553B'})
            
            fig.update_layout(xaxis_title="Time (Hour)", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True, key="traffic_chart")

    with c2:
        st.subheader("📋 Activity Log")
        # Display latest logs
        display_cols = df_view[['timestamp', 'event_type', 'tracker_id']].head(10)
        # Format time to show only HH:MM:SS
        display_cols['timestamp'] = display_cols['timestamp'].dt.strftime('%H:%M:%S')
        st.dataframe(display_cols, use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------------
# 7. AUTO-REFRESH LOGIC
# --------------------------------------------------------------------------------
# This causes the script to rerun every 1 seconds
time.sleep(1)
st.rerun()