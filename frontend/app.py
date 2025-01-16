import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

# Configure page
st.set_page_config(
    page_title="Cryptocurrency Market Data",
    layout="wide"
)

# Backend API URL
BACKEND_URL = "http://localhost:8000"

# Update interval in seconds
UPDATE_INTERVAL = 5

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
    
    # Create columns for date and interval selection
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
    
    # Add auto-refresh checkbox
    auto_refresh = st.checkbox('Auto-refresh data', value=True)
    
    # Create a placeholder for the data
    table_placeholder = st.empty()
    
    while True:
        try:
            # Convert selected date to timestamp
            start_time = int(datetime.combine(selected_date, datetime.min.time()).timestamp() * 1000)
            
            # Fetch data with selected interval and start time
            response = requests.get(
                f"{BACKEND_URL}/get_top_coins",
                params={
                    "interval": selected_interval,
                    "start_time": start_time
                }
            )
            data = response.json()
            
            if isinstance(data, list):
                # Create DataFrame
                df = pd.DataFrame(data)
                
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
                
                # Display data
                table_placeholder.dataframe(styled_df, use_container_width=True)
            
            if auto_refresh:
                time.sleep(UPDATE_INTERVAL)
            else:
                break
                
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main() 