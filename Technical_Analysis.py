import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import date, timedelta
import plotly.graph_objects as go
import time
from requests.exceptions import RequestException
import ta  # Technical Analysis library
import requests  # Add this import for requests exceptions
from utils.stock_utils import StockDataFetcher

# Add these constants at the top with other imports
RETRY_DELAY = 2
MAX_RETRIES = 3
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

# Page config must be the first Streamlit command
st.set_page_config(page_title="Stock Trend Analysis", layout="wide")

# Move sidebar warning after page config
st.sidebar.warning("""
    ⚠️ Note: Yahoo Finance has rate limits.
    If you encounter errors, please wait a few seconds before trying again.
""")

# Add CSS for better styling
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="big-font">Stock Trend Analysis & Prediction</p>', unsafe_allow_html=True)

# Add this after the title
st.markdown("""
    ### How to use:
    1. Enter a valid stock symbol (e.g., AAPL for Apple, MSFT for Microsoft)
    2. Select the time period you want to analyze
    3. Choose technical indicators to display
    
    Common stock symbols:
    - AAPL (Apple)
    - MSFT (Microsoft)
    - GOOGL (Google)
    - AMZN (Amazon)
    - META (Meta/Facebook)
""")

# Add common stock symbols dictionary
COMMON_SYMBOLS = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'META': 'Meta Platforms Inc.',
    'TSLA': 'Tesla Inc.',
    'NVDA': 'NVIDIA Corporation',
}

# Create two columns for inputs
col1, col2 = st.columns(2)

# Update the ticker input section with enhanced validation
with col1:
    ticker = st.text_input(
        'Enter Stock Symbol (e.g., AAPL, MSFT, GOOGL):',
        '',
        help="Enter a valid stock symbol. For example: AAPL for Apple, MSFT for Microsoft"
    ).upper().strip()
    
    # Enhanced validation with common symbol suggestion
    if ticker:
        if not ticker.isalpha():
            st.error("Stock symbol should only contain letters")
            st.stop()
        elif len(ticker) > 5:
            st.error("Stock symbol should not be longer than 5 characters")
            st.stop()
        elif ticker not in COMMON_SYMBOLS and ticker + 'L' in COMMON_SYMBOLS:
            st.warning(f"Did you mean {ticker + 'L'}? ({COMMON_SYMBOLS[ticker + 'L']})")
        elif ticker + 'A' in COMMON_SYMBOLS:
            st.warning(f"Did you mean {ticker + 'A'}? ({COMMON_SYMBOLS[ticker + 'A']})")
        
        # Show company name if it's a common symbol
        if ticker in COMMON_SYMBOLS:
            st.success(f"Loading data for {COMMON_SYMBOLS[ticker]}")

    # Add period selector
    time_period = st.selectbox(
        "Select Time Period",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "5 Years"]
    )

with col2:
    # Add technical indicator selection
    moving_average = st.multiselect(
        'Select Moving Averages',
        ['20 MA', '50 MA', '100 MA', '200 MA'],
        default=['50 MA', '200 MA']
    )
    
    # Fix the indicators multiselect by removing the invalid default value
    indicators = st.multiselect(
        'Select Technical Indicators',
        options=['RSI', 'MACD', 'Bollinger Bands'],
        default=[]  # Empty list is a valid default
    )
    
    # Add RSI period selection if RSI is selected
    if 'RSI' in indicators:
        rsi_period = st.slider('RSI Period', min_value=7, max_value=21, value=14)

# Calculate start date based on selected period
period_dict = {
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "1 Year": 365,
    "2 Years": 730,
    "5 Years": 1825
}
start_date = date.today() - timedelta(days=period_dict[time_period])
end_date = date.today()

@st.cache_data(ttl=3600)
def load_data(ticker: str, start_date: date, end_date: date) -> tuple:
    """Load stock data with improved error handling."""
    if not ticker:
        return None, None
    
    with st.spinner(f'Loading data for {ticker}...'):
        try:
            if 'last_error' in st.session_state:
                time.sleep(2)
                del st.session_state.last_error
            
            data, info = StockDataFetcher.fetch_stock_data(ticker, start_date, end_date)
            
            if data is not None:
                return data, info
            else:
                st.session_state.last_error = True
                return None, None
                
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            st.session_state.last_error = True
            return None, None

# Get selected ticker
if ticker:
    with st.spinner(f'Loading data for {ticker}...'):
        try:
            # Add delay if previous attempt failed
            if 'last_error' in st.session_state:
                time.sleep(2)
                del st.session_state.last_error
                
            data, info = StockDataFetcher.fetch_stock_data(ticker, start_date, end_date)
            
            if data is not None:
                # Display stock info
                current_price = data['Close'].iloc[-1]
                st.metric("Current Price", f"${current_price:.2f}")
                
                # Create price chart
                fig = go.Figure()
                
                # Add candlestick chart
                fig.add_trace(go.Candlestick(
                    x=data['Date'],
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='OHLC'
                ))
                
                # Add any selected indicators here...
                
                fig.update_layout(
                    title=f"{ticker} Stock Price",
                    yaxis_title="Price (USD)",
                    xaxis_title="Date",
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.last_error = True

else:
    st.error("Please enter a valid stock symbol")

# Add footer with disclaimer
st.markdown("""
---
**Disclaimer:** This tool is for educational purposes only. Do not use it as financial advice.
Stock data is provided by Yahoo Finance.
""")
