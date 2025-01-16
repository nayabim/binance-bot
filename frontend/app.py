import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from threading import Thread

# Initialize FastAPI app
api = FastAPI()
# ... your backend code here ...

# Start the FastAPI server in a separate thread
def run_api():
    uvicorn.run(api, host="127.0.0.1", port=8000)

Thread(target=run_api, daemon=True).start()

# Use localhost for the backend URL
BACKEND_URL = "http://127.0.0.1:8000"

# Configure page
st.set_page_config(
    page_title="Cryptocurrency Market Data",
    layout="wide"
)

# Update interval in seconds
UPDATE_INTERVAL = 5

def create_data_table(df):
    # Format the columns
    display_df = pd.DataFrame()
    display_df['Time'] = df['timestamp']
    display_df['Symbol'] = df.apply(lambda x: f"{x['symbol']} ({x['name']})", axis=1)
    display_df['Open'] = df['open'].apply(lambda x: f"{x:.2f}")
    display_df['High'] = df['high'].apply(lambda x: f"{x:.2f}")
    display_df['Low'] = df['low'].apply(lambda x: f"{x:.2f}")
    display_df['Close'] = df['close'].apply(lambda x: f"{x:.2f}")
    display_df['CHANGE'] = df['change'].apply(lambda x: f"{x:+.2f}%")
    display_df['MA(7)'] = df['ma7'].apply(lambda x: f"{x:.2f}")
    display_df['MA(25)'] = df['ma25'].apply(lambda x: f"{x:.2f}")
    display_df['MA(99)'] = df['ma99'].apply(lambda x: f"{x:.2f}")
    
    # Style the DataFrame
    def style_negative_red(val):
        try:
            if '%' in str(val):
                num = float(val.strip('%'))
                color = '#F6465D' if num < 0 else '#0ECB81' if num > 0 else ''
                return f'color: {color}'
        except:
            return ''

    # Apply styling
    styled_df = display_df.style.applymap(
        style_negative_red,
        subset=['CHANGE']
    )
    
    return styled_df

def main():
    st.markdown("""
    <style>
    .dataframe {
        font-size: 14px;
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    [data-testid="stDataFrame"] div[style*="overflow"] {
        height: calc(100vh - 250px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Cryptocurrency Market Data")
    
    # Add a connection status indicator
    if st.sidebar.checkbox("Show Backend Status"):
        try:
            response = requests.get(f"{BACKEND_URL}/health")  # Add a health check endpoint
            if response.status_code == 200:
                st.sidebar.success("Connected to backend")
            else:
                st.sidebar.error("Backend connection issues")
        except Exception as e:
            st.sidebar.error(f"Cannot connect to backend: {str(e)}")
    
    # Create tabs
    real_time_tab, historical_tab = st.tabs(["Real-time Data", "Historical Data"])
    
    # Create columns for date and interval selection
    with historical_tab:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_date = st.date_input(
                "Select Date",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
        
        with col2:
            try:
                # Fetch available intervals
                intervals_response = requests.get(f"{BACKEND_URL}/get_intervals")
                if intervals_response.status_code == 200:
                    intervals = intervals_response.json()
                    selected_interval = st.selectbox(
                        "Select Candle Interval",
                        options=list(intervals.keys()),
                        format_func=lambda x: intervals[x],
                        index=8  # Default to 4h
                    )
                else:
                    st.error("Failed to fetch intervals")
                    selected_interval = "4h"
            except Exception as e:
                st.error(f"Failed to fetch intervals: {str(e)}")
                selected_interval = "4h"
        
        # Create a placeholder for historical data
        historical_placeholder = st.empty()
    
    # Real-time tab content
    with real_time_tab:
        # Add auto-refresh checkbox
        auto_refresh = st.checkbox('Auto-refresh data', value=True)
        
        # Create a placeholder for real-time data
        realtime_placeholder = st.empty()
    
    # Main data loop
    while True:
        try:
            # Handle Historical Data
            with historical_tab:
                # Convert selected date to timestamp
                start_time = int(datetime.combine(selected_date, datetime.min.time()).timestamp() * 1000)
                
                # Fetch historical data
                hist_response = requests.get(
                    f"{BACKEND_URL}/get_top_coins",
                    params={
                        "interval": selected_interval,
                        "start_time": start_time
                    }
                )
                hist_data = hist_response.json()
                
                if isinstance(hist_data, list):
                    df_hist = pd.DataFrame(hist_data)
                    styled_hist_df = create_data_table(df_hist)
                    historical_placeholder.dataframe(styled_hist_df, use_container_width=True)
            
            # Handle Real-time Data
            with real_time_tab:
                # Fetch real-time data
                rt_response = requests.get(
                    f"{BACKEND_URL}/get_top_coins",
                    params={"interval": "4h"}  # Always use 4h for real-time
                )
                rt_data = rt_response.json()
                
                if isinstance(rt_data, list):
                    df_rt = pd.DataFrame(rt_data)
                    styled_rt_df = create_data_table(df_rt)
                    realtime_placeholder.dataframe(styled_rt_df, use_container_width=True)
            
            if auto_refresh:
                time.sleep(UPDATE_INTERVAL)
            else:
                break
                
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main() 