import streamlit as st
from newsapi import NewsApiClient
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Sector Sentiment Analysis",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .sector-box {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        background-color: rgba(28, 131, 225, 0.1);
    }
    .sentiment-indicator {
        font-size: 1.2em;
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 5px;
    }
    .bullish { color: #00ff00; }
    .bearish { color: #ff0000; }
    .neutral { color: #808080; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_news(sector: str, days: int = 7) -> list:
    """Fetch recent news articles for a given sector."""
    try:
        newsapi = NewsApiClient(api_key='24f63e7ed5f2419dad3349ed302267f4')  # Replace with your key
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Add 'stock market' to improve relevance
        query = f"{sector} sector stock market"
        
        articles = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='publishedAt',
            from_param=start_date.strftime('%Y-%m-%d'),
            to=end_date.strftime('%Y-%m-%d'),
            page_size=10
        )
        
        return articles['articles']
    except Exception as e:
        st.error(f"Failed to fetch sector news: {str(e)}")
        return []

def analyze_sentiment(text: str) -> float:
    """Analyze sentiment using VADER."""
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)['compound']

def classify_sentiment(score: float) -> tuple:
    """Classify sentiment score into label and CSS class."""
    if score >= 0.05:
        return "Bullish 📈", "bullish"
    elif score <= -0.05:
        return "Bearish 📉", "bearish"
    else:
        return "Neutral ➖", "neutral"

def main():
    st.title("📊 Sector Sentiment Analysis")
    
    # Define major market sectors
    sectors = [
        "Technology", "Healthcare", "Finance", "Energy",
        "Consumer", "Industrial", "Materials", "Real Estate",
        "Utilities", "Communications"
    ]
    
    # Sidebar controls
    with st.sidebar:
        selected_sectors = st.multiselect(
            "Select Sectors to Analyze:",
            sectors,
            default=["Technology", "Finance"]
        )
        days = st.slider("Analysis Period (days):", 1, 30, 7)
        st.info("💡 Select multiple sectors for comparison")
    
    if selected_sectors:
        # Create columns for sector analysis
        cols = st.columns(2)
        
        for idx, sector in enumerate(selected_sectors):
            with cols[idx % 2]:
                st.markdown(f"### {sector} Sector")
                
                with st.spinner(f"Analyzing {sector} sector..."):
                    articles = fetch_news(sector, days)
                    
                    if articles:
                        # Calculate sector sentiment
                        sentiments = [analyze_sentiment(art['title'] + ' ' + art.get('description', ''))
                                    for art in articles]
                        avg_sentiment = np.mean(sentiments)
                        label, sentiment_class = classify_sentiment(avg_sentiment)
                        
                        # Display sector sentiment
                        st.markdown(f"""
                            <div class='sector-box'>
                                <span class='sentiment-indicator {sentiment_class}'>
                                    {label} ({avg_sentiment:.3f})
                                </span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Plot sentiment distribution
                        fig = go.Figure()
                        fig.add_trace(go.Histogram(
                            x=sentiments,
                            nbinsx=20,
                            name=sector
                        ))
                        fig.update_layout(
                            title=f"{sector} Sentiment Distribution",
                            showlegend=True,
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display recent headlines
                        with st.expander("Recent Headlines"):
                            for article in articles[:5]:
                                sentiment = analyze_sentiment(article['title'])
                                label, _ = classify_sentiment(sentiment)
                                st.markdown(f"""
                                    - {article['title']} 
                                    *({label} | {sentiment:.2f})*
                                """)
                    else:
                        st.warning(f"No recent news found for {sector} sector")

if __name__ == "__main__":
    main()