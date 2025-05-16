import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Define time intervals
TIME_INTERVALS = {
    "1 Minute": "1m",
    "5 Minutes": "5m",
    "15 Minutes": "15m",
    "30 Minutes": "30m",
    "1 Hour": "1h",
    "1 Day": "1d",
    "1 Week": "1wk",
    "1 Month": "1mo"
}

# Maximum periods for each interval (Yahoo Finance limits)
MAX_PERIODS = {
    "1m": 7,      # 7 days
    "5m": 60,     # 60 days
    "15m": 60,    # 60 days
    "30m": 60,    # 60 days
    "1h": 730,    # 730 days
    "1d": 1825,   # 5 years
    "1wk": 3650,  # 10 years
    "1mo": 3650   # 10 years
}

MARKET_SPECIFIC_INTERVALS = {
    "US": list(TIME_INTERVALS.keys()),  # All intervals available
    "IN": ["1 Day", "1 Week", "1 Month"]  # Limited intervals for Indian stocks
}

def is_indian_stock(ticker: str) -> bool:
    """Check if the ticker is an Indian stock."""
    return ticker.endswith('.NS') or ticker.endswith('.BO')

def get_available_intervals(ticker: str) -> list:
    """Get available intervals based on the stock market."""
    return MARKET_SPECIFIC_INTERVALS["IN"] if is_indian_stock(ticker) else MARKET_SPECIFIC_INTERVALS["US"]

def load_data(ticker: str, interval: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Load stock data from Yahoo Finance with specified interval."""
    try:
        # Validate interval for Indian stocks
        if is_indian_stock(ticker) and interval in ["1m", "5m", "15m", "30m", "1h"]:
            st.error(f"Intraday data not available for Indian stocks. Please select daily or longer intervals.")
            return None
            
        # Adjust start date based on interval limits
        max_days = MAX_PERIODS[interval]
        adjusted_start = max(start_date, end_date - timedelta(days=max_days))
        
        df = yf.download(ticker, start=adjusted_start, end=end_date, interval=interval)
        if df.empty:
            st.error(f"""
                No data available for {ticker} at {interval} interval.
                {'Please use daily or longer intervals for Indian stocks.' if is_indian_stock(ticker) else ''}
            """)
            return None
            
        return df
    except Exception as e:
        st.error(f"""
            Error fetching data: {str(e)}
            Check if:
            1. The stock symbol is correct
            2. The selected interval is available for this stock
            3. The stock is actively traded
        """)
        return None

def main():
    st.title("🔮 Stock Price Prediction")
    
    # Sidebar inputs
    ticker = st.sidebar.text_input("Enter Stock Symbol:", "AAPL").upper()
    
    if ticker:
        # Get available intervals based on the stock market
        available_intervals = get_available_intervals(ticker)
        
        # Show market-specific guidance
        if is_indian_stock(ticker):
            st.sidebar.info("""
                ℹ️ Indian stocks (NSE/BSE) are limited to daily, weekly, and monthly intervals.
                Intraday data is not available.
            """)
        
        # Time interval selection with market-specific options
        interval_key = st.sidebar.selectbox(
            "Select Time Interval:",
            available_intervals
        )
        interval = TIME_INTERVALS[interval_key]
        
        # Adjust prediction period based on interval
        if interval in ["1m", "5m", "15m", "30m"]:
            default_periods = 24
            max_periods = 48
            period_unit = "hours"
        elif interval == "1h":
            default_periods = 7
            max_periods = 14
            period_unit = "days"
        else:
            default_periods = 30
            max_periods = 90
            period_unit = "periods"
        
        prediction_periods = st.sidebar.slider(
            f"Prediction {period_unit}:",
            1, max_periods, default_periods
        )
        
        lookback = st.sidebar.slider(
            "Lookback Periods:",
            10, 100, 30
        )
        
        # Calculate dates based on interval
        end_date = datetime.now()
        start_date = end_date - timedelta(days=MAX_PERIODS[interval])
        
        with st.spinner(f"Loading {interval_key} data for {ticker}..."):
            data = load_data(ticker, interval, start_date, end_date)
            
        if data is not None and not data.empty:
            # Prepare data and train model

            # Prepare data for LSTM
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data['Close'].values.reshape(-1, 1))

            X, y = [], []
            for i in range(lookback, len(scaled_data)):
                X.append(scaled_data[i - lookback:i, 0])
                y.append(scaled_data[i, 0])
            X, y = np.array(X), np.array(y)
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))

            # Build and train the LSTM model
            model = Sequential()
            model.add(LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], 1)))
            model.add(Dropout(0.2))
            model.add(LSTM(units=50, return_sequences=False))
            model.add(Dropout(0.2))
            model.add(Dense(units=1))
            model.compile(optimizer='adam', loss='mean_squared_error')
            model.fit(X, y, epochs=5, batch_size=32, verbose=0)

            # Predict future prices
            last_sequence = scaled_data[-lookback:]
            future_pred = []
            current_seq = last_sequence.copy()
            for _ in range(prediction_periods):
                pred = model.predict(current_seq.reshape(1, lookback, 1), verbose=0)
                future_pred.append(pred[0])
                current_seq = np.append(current_seq[1:], pred, axis=0)
            future_pred = scaler.inverse_transform(future_pred)

            # Add interval information to the plot
            # (You may want to add code here to plot the predictions if needed)
            # fig.update_layout(
            #     title=f"{ticker} Stock Price Prediction ({interval_key} intervals)",
            #     xaxis_title="Date/Time",
            #     yaxis_title="Price (USD)",
            #     hovermode='x unified'
            # )

            # Display additional metrics
            st.subheader("Prediction Details")
            cols = st.columns(4)
            
            with cols[0]:
                current_price = data['Close'][-1]
                st.metric("Current Price", f"${current_price:.2f}")
            
            with cols[1]:
                last_pred = future_pred[-1][0]
                change = ((last_pred - current_price) / current_price) * 100
                st.metric("Predicted Price", f"${last_pred:.2f}", f"{change:+.2f}%")
            
            with cols[2]:
                st.metric("Interval", interval_key)
            
            with cols[3]:
                confidence = "High" if abs(change) < 10 else "Medium" if abs(change) < 20 else "Low"
                st.metric("Confidence", confidence)
            
            # Add prediction disclaimer
            st.info(
                "⚠️ Disclaimer: Predictions are based on historical data and technical analysis. "
                "They should not be the sole basis for investment decisions."
            )

if __name__ == "__main__":
    main()