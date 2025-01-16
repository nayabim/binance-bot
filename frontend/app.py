import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import time
import plotly.graph_objects as go

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
    
    # Add date and interval selection in a row
    col1, col2 = st.columns(2)
    
    with col1:
        # Date selector (default to 7 days ago)
        default_date = (datetime.now() - timedelta(days=7)).date()
        selected_date = st.date_input(
            "Select Start Date",
            value=default_date,
            max_value=datetime.now().date()
        )
    
    with col2:
        try:
            intervals_response = requests.get(f"{BACKEND_URL}/get_intervals")
            if intervals_response.status_code == 200:
                intervals = intervals_response.json()
                selected_interval = st.selectbox(
                    "Select Candle Interval",
                    options=list(intervals.keys()),
                    format_func=lambda x: intervals[x],
                    index=6  # Default to 1h
                )
            else:
                st.error("Failed to fetch intervals from server")
                intervals = {"1h": "1 hour"}
                selected_interval = "1h"
        except Exception as e:
            st.error(f"Failed to fetch intervals: {str(e)}")
            intervals = {"1h": "1 hour"}
            selected_interval = "1h"

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Real-time Data", "Historical Data"])
    
    with tab1:
        # Your existing real-time data display code here
        table_placeholder = st.empty()
        
        while True:
            try:
                # Your existing real-time data fetching and display code
                response = requests.get(f"{BACKEND_URL}/get_top_coins")
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
                st.error(f"Error fetching real-time data: {str(e)}")
                time.sleep(5)
                
    with tab2:
        try:
            # Fetch historical data based on selections
            params = {
                'interval': selected_interval,
                'start_date': selected_date.strftime('%Y-%m-%d')
            }
            hist_response = requests.get(
                f"{BACKEND_URL}/get_historical_data",
                params=params
            )
            hist_data = hist_response.json()
            
            if hist_data:
                # Create DataFrame
                df_hist = pd.DataFrame(hist_data)
                df_hist['timestamp'] = pd.to_datetime(df_hist['timestamp'], unit='ms')
                
                # Format the data
                df_hist['volume_formatted'] = df_hist['volume'].apply(format_number)
                df_hist['close_formatted'] = df_hist['close'].apply(lambda x: f"${x:,.2f}")
                
                # Display historical data
                st.dataframe(
                    df_hist[[
                        'timestamp',
                        'close_formatted',
                        'high',
                        'low',
                        'volume_formatted'
                    ]].rename(columns={
                        'timestamp': 'Time',
                        'close_formatted': 'Close',
                        'high': 'High',
                        'low': 'Low',
                        'volume_formatted': 'Volume'
                    }),
                    use_container_width=True
                )
                
                # Add candlestick chart
                fig = go.Figure(data=[go.Candlestick(
                    x=df_hist['timestamp'],
                    open=df_hist['open'],
                    high=df_hist['high'],
                    low=df_hist['low'],
                    close=df_hist['close']
                )])
                
                fig.update_layout(
                    title=f"Historical Data ({selected_interval} candles)",
                    yaxis_title="Price",
                    xaxis_title="Date"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error fetching historical data: {str(e)}")

if __name__ == "__main__":
    main() 