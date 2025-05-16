import streamlit as st
from utils.stock_analyzer import StockAnalyzer
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Stock Analysis Terminal",
    page_icon="📈",
    layout="wide"
)

def main():
    st.title("📊 Stock Analysis & Investment Recommendation")
    
    # User input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symbol = st.text_input(
            "Enter Stock Symbol:",
            help="Example: AAPL for Apple, MSFT for Microsoft, TCS.NS for Tata Consultancy"
        ).upper()
        
    with col2:
        period = st.selectbox(
            "Analysis Period",
            ["1 Month", "3 Months", "6 Months", "1 Year"],
            index=3
        )
    
    if symbol:
        with st.spinner(f"Analyzing {symbol}..."):
            analyzer = StockAnalyzer(symbol)
            if analyzer.fetch_data(period="1y"):
                
                # Create tabs for different analyses
                overview_tab, technical_tab, fundamental_tab = st.tabs([
                    "Overview & Recommendation", "Technical Analysis", "Fundamental Analysis"
                ])
                
                with overview_tab:
                    # Get recommendation
                    recommendation, score, explanation = analyzer.get_investment_recommendation()
                    
                    # Display recommendation
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Recommendation", recommendation)
                        st.metric("Overall Score", f"{score:.1f}/100")
                    with col2:
                        st.info(explanation)
                    
                    # Display price chart
                    fig = go.Figure(data=[go.Candlestick(
                        x=analyzer.data.index,
                        open=analyzer.data['Open'],
                        high=analyzer.data['High'],
                        low=analyzer.data['Low'],
                        close=analyzer.data['Close']
                    )])
                    fig.update_layout(title=f"{symbol} Stock Price")
                    st.plotly_chart(fig, use_container_width=True)
                
                with technical_tab:
                    signals = analyzer.analyze_technicals()
                    
                    # Display technical signals
                    cols = st.columns(3)
                    for i, (signal, value) in enumerate(signals.items()):
                        with cols[i % 3]:
                            st.metric(signal.title(), str(value))
                
                with fundamental_tab:
                    metrics = analyzer.analyze_fundamentals()
                    
                    # Display fundamental metrics
                    cols = st.columns(3)
                    for i, (metric, value) in enumerate(metrics.items()):
                        with cols[i % 3]:
                            st.metric(
                                metric.replace('_', ' ').title(),
                                f"{value:.2f}" if isinstance(value, float) else str(value)
                            )
            else:
                st.error(f"Could not fetch data for {symbol}. Please verify the symbol.")
    
    else:
        st.info("""
        ### Welcome to Stock Analysis Terminal
        Enter a stock symbol above to get:
        - Investment recommendation
        - Technical analysis
        - Fundamental analysis
        - Price predictions
        
        Examples:
        - US Stocks: AAPL, MSFT, GOOGL
        - Indian Stocks: TCS.NS, RELIANCE.NS
        """)

if __name__ == "__main__":
    main()