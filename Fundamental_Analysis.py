import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Optional, List, Tuple
import time
from datetime import datetime, date
import numpy as np
import requests
from requests.exceptions import RequestException
from time import sleep
from utils.stock_utils import StockDataFetcher

# Constants
CACHE_TTL = 3600  # Cache timeout in seconds
COMMON_SYMBOLS = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'META': 'Meta Platforms Inc.',
}

# Page configuration
st.set_page_config(
    page_title="Fundamental Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-row {
        background-color: rgba(28, 131, 225, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0px;
    }
    .stMetric {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 5px;
    }
    /* New CSS for search results */
    .search-result {
        padding: 8px;
        margin: 4px 0;
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.05);
        cursor: pointer;
    }
    .search-result:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

def validate_ticker(symbol: str) -> bool:
    """Validate the input ticker symbol."""
    if not symbol:
        st.error("Please enter a stock symbol")
        return False
        
    # Remove common suffixes for validation
    base_symbol = symbol.split('.')[0]
    
    # Check base symbol contains valid characters
    if not base_symbol.replace('-', '').isalnum():
        st.error("Stock symbol should only contain letters, numbers, dots, and hyphens")
        return False
        
    # Allow longer symbols for international stocks
    if len(symbol) > 12:  # Increased max length
        st.error("Stock symbol is too long")
        return False
        
    # Validate common suffixes
    valid_suffixes = {'.NS', '.BO', '.L', '.PA', '.DE', '.HK'}
    if '.' in symbol:
        suffix = '.' + symbol.split('.')[1]
        if suffix not in valid_suffixes:
            st.warning(f"Unusual suffix detected. Common suffixes are: {', '.join(valid_suffixes)}")
            
    return True

@st.cache_data(ttl=CACHE_TTL)
def get_fundamentals(symbol: str) -> Optional[Dict]:
    """Fetch fundamental data using the shared utility."""
    if not StockDataFetcher.validate_ticker(symbol):
        st.error("Invalid stock symbol format")
        return None
    
    # Get today's date for a minimal data fetch
    today = date.today()
    data, info = StockDataFetcher.fetch_stock_data(symbol, today, today)
    
    return info if info else None

def format_large_number(num: float) -> str:
    """Format large numbers into readable format."""
    if num >= 1e12:
        return f"${num/1e12:.2f}T"
    if num >= 1e9:
        return f"${num/1e9:.2f}B"
    if num >= 1e6:
        return f"${num/1e6:.2f}M"
    return f"${num:.2f}"

def display_company_overview(info: Dict):
    """Display company overview metrics."""
    st.subheader('📈 Company Overview')
    with st.container():
        st.markdown('<div class="metric-row">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Market Cap", 
                format_large_number(info.get('marketCap', 0)),
                delta=None
            )
        with col2:
            st.metric(
                "P/E Ratio", 
                f"{info.get('trailingPE', 0):.2f}",
                delta=None
            )
        with col3:
            st.metric(
                "Dividend Yield", 
                f"{info.get('dividendYield', 0)*100:.2f}%",
                delta=None
            )
        st.markdown('</div>', unsafe_allow_html=True)

def display_financial_metrics(info: Dict):
    """Display financial metrics."""
    st.subheader('📊 Financial Metrics')
    metrics = {
        'Revenue Growth': info.get('revenueGrowth', 0) * 100,
        'Profit Margin': info.get('profitMargins', 0) * 100,
        'Return on Equity': info.get('returnOnEquity', 0) * 100
    }
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(metrics.keys()),
        y=list(metrics.values()),
        text=[f"{val:.2f}%" for val in metrics.values()],
        textposition='auto',
        marker_color=['rgb(26, 118, 255)', 'rgb(55, 183, 109)', 'rgb(255, 127, 14)']
    ))
    
    fig.update_layout(
        title='Key Financial Metrics',
        yaxis_title='Percentage (%)',
        template='plotly_white',
        height=400,
        showlegend=False,
        margin=dict(t=30, l=0, r=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.metric(
        "Debt to Equity Ratio",
        f"{info.get('debtToEquity', 0):.2f}",
        delta=None
    )

def display_ownership_info(stock: yf.Ticker):
    """Display major shareholders and institutional investors with visualizations."""
    st.subheader('👥 Ownership Information')
    
    holder_tabs = st.tabs(["Major Holders", "Institutional Holders", "Mutual Fund Holders"])
    
    with holder_tabs[0]:
        try:
            major_holders = stock.major_holders
            if not major_holders.empty:
                # Display data table
                st.dataframe(
                    major_holders,
                    column_config={
                        0: "Percentage",
                        1: "Holder Type"
                    },
                    use_container_width=True
                )
                
                # Create pie chart for major holders
                fig = go.Figure(data=[go.Pie(
                    labels=major_holders[1],
                    values=major_holders[0].str.rstrip('%').astype(float),
                    hole=0.4,
                    textinfo='label+percent',
                    textposition='inside',
                    marker=dict(colors=['rgb(26, 118, 255)', 'rgb(55, 183, 109)', 
                                      'rgb(255, 127, 14)', 'rgb(148, 103, 189)']),
                )])
                
                fig.update_layout(
                    title='Ownership Distribution',
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=400,
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No major holders data available")
        except Exception as e:
            st.warning("Could not fetch major holders data")
    
    with holder_tabs[1]:
        try:
            institutional_holders = stock.institutional_holders
            if institutional_holders is not None and not institutional_holders.empty:
                # Format data
                institutional_holders['Date Reported'] = pd.to_datetime(
                    institutional_holders['Date Reported']
                ).dt.strftime('%Y-%m-%d')
                
                # Create bar chart for top institutional holders
                fig = go.Figure()
                
                # Sort by shares and get top 10
                top_institutions = institutional_holders.nlargest(10, 'Shares')
                
                fig.add_trace(go.Bar(
                    x=top_institutions['Holder'],
                    y=top_institutions['Shares'],
                    text=[f"{x:,.0f}" for x in top_institutions['Shares']],
                    textposition='auto',
                    marker_color='rgb(26, 118, 255)',
                ))
                
                fig.update_layout(
                    title='Top 10 Institutional Holders',
                    xaxis_title='Institution',
                    yaxis_title='Number of Shares',
                    height=500,
                    xaxis_tickangle=-45,
                    showlegend=False,
                    margin=dict(b=100)  # Add bottom margin for rotated labels
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display detailed data table
                st.dataframe(
                    institutional_holders,
                    use_container_width=True,
                    column_config={
                        "Holder": "Institution Name",
                        "Shares": "Shares Held",
                        "Date Reported": "Report Date",
                        "Value": "Holdings Value",
                        "% Out": "% of Shares Outstanding"
                    }
                )
            else:
                st.info("No institutional holders data available")
        except Exception as e:
            st.warning(f"Could not fetch institutional holders data: {str(e)}")
    
    with holder_tabs[2]:
        try:
            mutualfund_holders = stock.mutualfund_holders
            if mutualfund_holders is not None and not mutualfund_holders.empty:
                # Create treemap for mutual fund holdings
                fig = go.Figure(go.Treemap(
                    labels=mutualfund_holders['Holder'],
                    parents=[''] * len(mutualfund_holders),
                    values=mutualfund_holders['Shares'],
                    textinfo='label+value',
                    hovertemplate='<b>%{label}</b><br>Shares: %{value:,.0f}<extra></extra>'
                ))
                
                fig.update_layout(
                    title='Mutual Fund Holdings Distribution',
                    height=600,
                    margin=dict(t=30, l=10, r=10, b=10)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display detailed data table
                mutualfund_holders['Date Reported'] = pd.to_datetime(
                    mutualfund_holders['Date Reported']
                ).dt.strftime('%Y-%m-%d')
                
                st.dataframe(
                    mutualfund_holders,
                    use_container_width=True,
                    column_config={
                        "Holder": "Fund Name",
                        "Shares": "Shares Held",
                        "Date Reported": "Report Date",
                        "Value": "Holdings Value",
                        "% Out": "% of Shares Outstanding"
                    }
                )
            else:
                st.info("No mutual fund holders data available")
        except Exception as e:
            st.warning("Could not fetch mutual fund holders data")

def search_stocks(query: str) -> List[Tuple[str, str]]:
    """Search for stocks by name or symbol."""
    try:
        # Yahoo Finance API endpoint for stock search
        url = f"https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            'q': query,
            'quotesCount': 10,
            'newsCount': 0,
            'enableFuzzyQuery': True,
            'quotesQueryId': 'tss_match_phrase_query'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        }
        
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        
        if 'quotes' in data and data['quotes']:
            return [(quote['symbol'], quote.get('longname', quote.get('shortname', ''))) 
                   for quote in data['quotes'] 
                   if quote.get('quoteType') == 'EQUITY']
        return []
        
    except Exception as e:
        st.error(f"Error searching for stocks: {str(e)}")
        return []

def main():
    st.markdown("# 📊 Fundamental Analysis")
    
    # Add search functionality in sidebar
    search_col1, search_col2 = st.sidebar.columns([3, 1])
    
    with search_col1:
        search_query = st.text_input(
            "Search by company name or symbol:",
            help="Enter company name or stock symbol (e.g., 'Apple' or 'AAPL')"
        )
    
    with search_col2:
        if st.button("🔍 Search"):
            if search_query:
                with st.spinner("Searching..."):
                    results = search_stocks(search_query)
                    if results:
                        # Store results in session state
                        st.session_state.search_results = results
                    else:
                        st.sidebar.warning("No results found")
    
    # Display search results and allow selection
    if hasattr(st.session_state, 'search_results'):
        st.sidebar.subheader("Search Results:")
        for symbol, name in st.session_state.search_results:
            if st.sidebar.button(f"{name} ({symbol})", key=f"btn_{symbol}"):
                ticker = symbol
                st.session_state.selected_ticker = symbol
                st.session_state.selected_company = name
    
    # Get selected ticker
    ticker = getattr(st.session_state, 'selected_ticker', None)
    
    if ticker:
        st.sidebar.success(f"Selected: {st.session_state.selected_company} ({ticker})")
        
        with st.spinner(f'Fetching fundamental data for {ticker}...'):
            stock = yf.Ticker(ticker)
            info = get_fundamentals(ticker)
            
        if info:
            display_company_overview(info)
            
            # Company Description
            with st.expander("Company Description", expanded=False):
                st.write(info.get('longBusinessSummary', 'No description available.'))
            
            # Financial Metrics
            display_financial_metrics(info)
            
            # Ownership Information
            display_ownership_info(stock)
    else:
        st.sidebar.info("""
            👆 Search for a company by name or stock symbol above.
            
            Examples:
            - Company names: 'Apple', 'Microsoft', 'Tesla'
            - Stock symbols: 'AAPL', 'MSFT', 'TSLA'
        """)

if __name__ == "__main__":
    main()