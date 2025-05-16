import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, timedelta
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, Optional, Tuple, List

class StockAnalyzer:
    def __init__(self, symbol: str):
        self.symbol = symbol.upper().strip()
        self.stock = yf.Ticker(self.symbol)
        self.data = None
        self.info = None
        self.sentiment_score = 0
        self.technical_signals = {}
        self.fundamental_metrics = {}
        
    def fetch_data(self, period: str = "1y") -> bool:
        """Fetch stock data and basic info."""
        try:
            self.data = self.stock.history(period=period)
            if self.data.empty:
                return False
            
            self.info = self.stock.info
            return True
        except Exception:
            return False
    
    def analyze_technicals(self) -> Dict:
        """Perform technical analysis."""
        if self.data is None:
            return {}
            
        # Calculate technical indicators
        close_prices = self.data['Close']
        sma_50 = close_prices.rolling(window=50).mean()
        sma_200 = close_prices.rolling(window=200).mean()
        rsi = self._calculate_rsi(close_prices)
        
        current_price = close_prices[-1]
        
        self.technical_signals = {
            'trend': 'Bullish' if sma_50[-1] > sma_200[-1] else 'Bearish',
            'rsi_signal': 'Oversold' if rsi[-1] < 30 else 'Overbought' if rsi[-1] > 70 else 'Neutral',
            'price_trend': 'Up' if current_price > sma_50[-1] else 'Down',
            'support_level': self._find_support(),
            'resistance_level': self._find_resistance()
        }
        
        return self.technical_signals
    
    def analyze_fundamentals(self) -> Dict:
        """Analyze fundamental metrics."""
        if not self.info:
            return {}
            
        self.fundamental_metrics = {
            'pe_ratio': self.info.get('forwardPE', 0),
            'peg_ratio': self.info.get('pegRatio', 0),
            'profit_margin': self.info.get('profitMargins', 0),
            'debt_to_equity': self.info.get('debtToEquity', 0),
            'return_on_equity': self.info.get('returnOnEquity', 0),
            'quick_ratio': self.info.get('quickRatio', 0)
        }
        
        return self.fundamental_metrics
    
    def get_investment_recommendation(self) -> Tuple[str, float, str]:
        """Generate investment recommendation based on all analyses."""
        if not all([self.technical_signals, self.fundamental_metrics]):
            return "Insufficient Data", 0, "Unable to make recommendation due to limited data"
        
        # Score calculation (0-100)
        technical_score = self._calculate_technical_score()
        fundamental_score = self._calculate_fundamental_score()
        sentiment_score = self.sentiment_score
        
        total_score = (technical_score * 0.4 + 
                      fundamental_score * 0.4 + 
                      sentiment_score * 0.2)
        
        # Generate recommendation
        if total_score >= 70:
            recommendation = "Strong Buy"
            explanation = "Strong technical signals and fundamentals support buying"
        elif total_score >= 60:
            recommendation = "Buy"
            explanation = "Generally positive indicators with some caution"
        elif total_score >= 40:
            recommendation = "Hold"
            explanation = "Mixed signals suggest holding current position"
        elif total_score >= 30:
            recommendation = "Sell"
            explanation = "Weak performance indicators suggest selling"
        else:
            recommendation = "Strong Sell"
            explanation = "Multiple negative indicators suggest immediate selling"
            
        return recommendation, total_score, explanation
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI technical indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _find_support(self) -> float:
        """Find recent support level."""
        return self.data['Low'].tail(20).min()
    
    def _find_resistance(self) -> float:
        """Find recent resistance level."""
        return self.data['High'].tail(20).max()
    
    def _calculate_technical_score(self) -> float:
        """Calculate technical analysis score (0-100)."""
        score = 50  # Base score
        
        if self.technical_signals['trend'] == 'Bullish':
            score += 15
        if self.technical_signals['rsi_signal'] == 'Oversold':
            score += 10
        if self.technical_signals['price_trend'] == 'Up':
            score += 15
            
        return min(max(score, 0), 100)
    
    def _calculate_fundamental_score(self) -> float:
        """Calculate fundamental analysis score (0-100)."""
        score = 50  # Base score
        
        # PE Ratio analysis
        pe = self.fundamental_metrics['pe_ratio']
        if 10 <= pe <= 25:
            score += 10
        
        # Profit margin analysis
        profit_margin = self.fundamental_metrics['profit_margin']
        if profit_margin > 0.2:
            score += 10
            
        # Debt analysis
        debt_ratio = self.fundamental_metrics['debt_to_equity']
        if debt_ratio < 1:
            score += 10
            
        return min(max(score, 0), 100)