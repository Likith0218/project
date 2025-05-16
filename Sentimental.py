import streamlit as st
from newsapi import NewsApiClient
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Sentiment Analysis",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .sentiment-box {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .bullish {
        background-color: rgba(0, 255, 0, 0.1);
    }
    .bearish {
        background-color: rgba(255, 0, 0, 0.1);
    }
    .neutral {
        background-color: rgba(128, 128, 128, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_news(company: str, days: int = 7) -> list:
    """Fetch recent news articles for a given company."""
    try:
        newsapi = NewsApiClient(api_key='24f63e7ed5f2419dad3349ed302267f4')  # Replace with your key
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        articles = newsapi.get_everything(
            q=company,
            language='en',
            sort_by='publishedAt',
            from_param=start_date.strftime('%Y-%m-%d'),
            to=end_date.strftime('%Y-%m-%d'),
            page_size=10
        )
        
        return [{
            'title': article['title'],
            'description': article['description'],
            'url': article['url'],
            'publishedAt': article['publishedAt'],
            'source': article['source']['name']
        } for article in articles['articles']]
    except Exception as e:
        st.error(f"Failed to fetch news: {str(e)}")
        return []

def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment using VADER."""
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)

def classify_sentiment(score: float) -> tuple:
    """Classify sentiment score into labels with colors."""
    if score >= 0.05:
        return "Bullish 📈", "bullish", "green"
    elif score <= -0.05:
        return "Bearish 📉", "bearish", "red"
    else:
        return "Neutral ➖", "neutral", "gray"

def main():
    st.title("🔍 Stock Sentiment Analysis")
    
    # Sidebar inputs
    with st.sidebar:
        company = st.text_input("Enter Company Name/Symbol:", "AAPL")
        days = st.slider("Analysis Period (days):", 1, 30, 7)
        st.info("💡 Try both company name and symbol for better results")
    
    if company:
        with st.spinner(f"Analyzing sentiment for {company}..."):
            articles = fetch_news(company, days)
            
            if articles:
                # Calculate overall sentiment
                sentiments = [analyze_sentiment(article['title'])['compound'] 
                            for article in articles]
                avg_sentiment = np.mean(sentiments)
                label, class_name, color = classify_sentiment(avg_sentiment)
                
                # Display overall sentiment
                st.subheader("Overall Market Sentiment")
                st.markdown(f"""
                    <div class='sentiment-box {class_name}'>
                        <h3 style='color: {color}'>{label}</h3>
                        <p>Sentiment Score: {avg_sentiment:.3f}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Plot sentiment distribution
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=sentiments,
                    nbinsx=20,
                    marker_color=color,
                    opacity=0.7
                ))
                fig.update_layout(
                    title="Sentiment Distribution",
                    xaxis_title="Sentiment Score",
                    yaxis_title="Count",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display news articles with individual sentiment
                st.subheader("Recent News Articles")
                for article in articles:
                    sentiment = analyze_sentiment(article['title'])['compound']
                    _, _, color = classify_sentiment(sentiment)
                    
                    st.markdown(f"""
                        <div style='padding: 10px; border-left: 5px solid {color}; margin: 10px 0;'>
                            <h4>{article['title']}</h4>
                            <p>{article['description']}</p>
                            <small>Source: {article['source']} | 
                                   Published: {article['publishedAt']} | 
                                   Sentiment: {sentiment:.3f}</small><br>
                            <a href='{article['url']}' target='_blank'>Read More</a>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No recent news articles found. Try a different company name or symbol.")

if __name__ == "__main__":
    main()