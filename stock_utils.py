import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from typing import Optional, Dict, Tuple
import time

class StockDataFetcher:
    @staticmethod
    def validate_ticker(symbol: str) -> bool:
        """Validate ticker symbol."""
        if not symbol:
            st.error("Please enter a stock symbol")
            return False
        
        symbol = symbol.strip().upper()
        base_symbol = symbol.split('.')[0]
        
        if not base_symbol.replace('-', '').isalnum():
            st.error("Stock symbol should only contain letters, numbers, and hyphens")
            return False
            
        if '.' in symbol:
            valid_suffixes = {'.NS', '.BO', '.L', '.PA', '.DE', '.HK'}
            suffix = '.' + symbol.split('.')[1]
            if suffix not in valid_suffixes and len(symbol) > 6:
                st.error(f"Invalid suffix. Valid suffixes are: {', '.join(valid_suffixes)}")
                return False
        elif len(symbol) > 5:
            st.error("US stock symbols should not be longer than 5 characters")
            return False
            
        return True

    @staticmethod
    @st.cache_data(ttl=1800)
    def fetch_stock_data(symbol: str, start_date: date, end_date: date) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
        """Fetch stock data with improved reliability."""
        if not StockDataFetcher.validate_ticker(symbol):
            return None, None

        try:
            # Initialize ticker
            stock = yf.Ticker(symbol)
            
            # Get a quick quote first
            try:
                data = stock.history(period='1d')
                if data.empty:
                    st.error(f"No data available for {symbol}")
                    return None, None
            except Exception as e:
                st.error(f"Error validating {symbol}: {str(e)}")
                return None, None

            # Get full historical data
            try:
                data = stock.history(
                    start=start_date,
                    end=end_date,
                    interval='1d'
                )
                
                if data.empty:
                    st.error(f"No historical data found for {symbol}")
                    return None, None
                    
                data = data.reset_index()
                
                # Try to get company info
                try:
                    info = stock.info
                except:
                    info = {}
                    st.warning(f"Limited company information available for {symbol}")
                
                return data, info
                
            except Exception as e:
                st.error(f"Error fetching historical data: {str(e)}")
                return None, None
                
        except Exception as e:
            st.error(f"""
            Failed to fetch data for {symbol}.
            Please:
            1. Verify the stock symbol
            2. Try again in a few minutes (rate limiting)
            3. Check if the market is open
            
            Error: {str(e)}
            """)
            return None, None