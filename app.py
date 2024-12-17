from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
import os
import numpy as np
from textblob import TextBlob

load_dotenv()

app = Flask(__name__)

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
STOCKS_API_KEY = os.getenv("STOCKS_API_KEY")

# Base URLs
NEWS_API_URL = "https://newsapi.org/v2/everything"
STOCKS_API_URL = "https://www.alphavantage.co/query"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/market')
def market():
    return render_template('market.html')

@app.route('/search')
def search():
    company = request.args.get('company')
    if not company:
        return jsonify({"error": "Company parameter is required"}), 400

    try:
        # Fetch current stock price and historical data
        stock_data = get_stock_data(company)
        if not stock_data:
            return jsonify({"error": "Stock data not found"}), 404

        current_price = stock_data["current_price"]
        historical_data = stock_data["historical_data"]

        # Fetch news articles
        news = get_news(company)
        if not news:
            return jsonify({"error": "News articles not found"}), 404

        # Analyze the investment
        suggestion = analyze_investment(historical_data, current_price, news)

        return jsonify({
            "company": company,
            "current_price": current_price,
            "historical_data": historical_data,
            "news": news,
            "suggestion": suggestion
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/market_news')
def market_news():
    try:
        # Fetch market news
        news_articles = fetch_market_news()
        
        if not news_articles:
            return jsonify({"error": "No news articles found"}), 404
            
        return jsonify({
            "articles": news_articles
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/market_analysis')
def market_analysis():
    try:
        # Fetch market news for sentiment analysis
        news_articles = fetch_market_news()
        
        # Analyze news sentiment
        news_analysis = {
            "categorized_articles": {
                "positive": [],
                "neutral": [],
                "negative": []
            },
            "sentiment_stats": {
                "positive_count": 0,
                "neutral_count": 0,
                "negative_count": 0,
                "average": 0
            }
        }

        total_sentiment = 0
        for article in news_articles:
            sentiment = TextBlob(article.get('summary', '')).sentiment.polarity
            
            # Categorize article based on sentiment
            if sentiment > 0.1:
                news_analysis["categorized_articles"]["positive"].append(article)
                news_analysis["sentiment_stats"]["positive_count"] += 1
            elif sentiment < -0.1:
                news_analysis["categorized_articles"]["negative"].append(article)
                news_analysis["sentiment_stats"]["negative_count"] += 1
            else:
                news_analysis["categorized_articles"]["neutral"].append(article)
                news_analysis["sentiment_stats"]["neutral_count"] += 1
                
            total_sentiment += sentiment

        # Calculate average sentiment
        total_articles = len(news_articles)
        if total_articles > 0:
            news_analysis["sentiment_stats"]["average"] = total_sentiment / total_articles

        # Generate market outlook
        market_outlook = {
            "outlook": "Bullish" if total_sentiment > 0 else "Bearish" if total_sentiment < 0 else "Neutral",
            "confidence": "High" if total_articles >= 5 else "Moderate" if total_articles >= 3 else "Low",
            "summary": generate_market_summary(total_sentiment, total_articles)
        }
        news_analysis["market_outlook"] = market_outlook

        # Generate stock analysis
        stock_analysis = {
            "market_stats": {
                "current_price": 0,
                "30_day_return": 0,
                "volatility": 0,
                "sharpe_ratio": 0,
                "trend": "Neutral"
            },
            "technical_analysis": {
                "summary": "Market analysis temporarily unavailable",
                "risk_level": "Moderate"
            }
        }

        try:
            # Fetch S&P 500 data for market stats
            spy_data = get_stock_data("SPY")
            if spy_data:
                stock_analysis["market_stats"].update({
                    "current_price": spy_data["current_price"],
                    "30_day_return": calculate_return(spy_data["historical_data"]),
                    "volatility": calculate_volatility(spy_data["historical_data"]),
                    "trend": determine_trend(spy_data["historical_data"])
                })
                
                stock_analysis["technical_analysis"] = {
                    "summary": generate_technical_summary(stock_analysis["market_stats"]),
                    "risk_level": determine_risk_level(stock_analysis["market_stats"]["volatility"])
                }
        except Exception as e:
            print(f"Error fetching market stats: {e}")

        return jsonify({
            "news_analysis": news_analysis,
            "stock_analysis": stock_analysis
        })

    except Exception as e:
        print(f"Market analysis error: {e}")
        return jsonify({"error": str(e)}), 500

def get_stock_data(company):
    """
    Fetch stock data including current price and historical data from the Stocks API.
    """
    try:
        # Fetch current stock price
        current_price_response = requests.get(
            STOCKS_API_URL,
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": company,
                "apikey": STOCKS_API_KEY
            }
        )
        
        if current_price_response.status_code != 200:
            return None

        current_price_data = current_price_response.json()
        try:
            current_price = float(current_price_data["Global Quote"]["05. price"])
        except (KeyError, ValueError):
            return None

        # Fetch historical stock data (5 years)
        historical_response = requests.get(
            STOCKS_API_URL,
            params={
                "function": "TIME_SERIES_MONTHLY_ADJUSTED",
                "symbol": company,
                "apikey": STOCKS_API_KEY
            }
        )
        
        if historical_response.status_code != 200:
            return None

        historical_data = historical_response.json().get("Monthly Adjusted Time Series", {})

        # Process the historical data
        processed_data = []
        for date, data in historical_data.items():
            processed_data.append({
                "date": date,
                "price": float(data["4. close"])
            })

        # Limit to the most recent 60 months (5 years)
        processed_data = processed_data[:60]

        return {
            "current_price": current_price,
            "historical_data": processed_data
        }

    except Exception as e:
        print(f"Error fetching stock data: {str(e)}")
        return None

def get_news(company):
    """
    Fetch top 5 news articles about the company using the News API.
    """
    try:
        response = requests.get(
            NEWS_API_URL,
            params={
                "q": company,
                "apiKey": NEWS_API_KEY,
                "pageSize": 5,
                "sortBy": "relevance"
            }
        )
        
        if response.status_code != 200:
            return None

        articles = response.json().get("articles", [])
        news_data = [
            {
                "title": article["title"],
                "url": article["url"]
            }
            for article in articles
        ]
        return news_data

    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return None

def analyze_investment(historical_data, current_price, news):
    """
    Analyze stock trends and news sentiment to provide an investment suggestion.
    """
    try:
        # Analyze historical data (growth trend)
        if not historical_data:
            return "Insufficient data"
            
        prices = [entry["price"] for entry in historical_data]
        if not prices:
            return "Insufficient price data"
            
        growth_rate = (prices[0] - prices[-1]) / prices[-1] * 100

        # Simple analysis logic
        if growth_rate > 20 and len(news) >= 3:
            return "Invest"
        elif growth_rate > 0:
            return "Hold"
        else:
            return "Avoid"
            
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        return "Analysis Error"

def fetch_market_news():
    """
    Fetch recent news articles related to overall stock market growth.
    """
    try:
        response = requests.get(
            NEWS_API_URL,
            params={
                "q": "stock market",  # Broadened search term
                "sortBy": "publishedAt",  # Get latest news
                "language": "en",
                "apiKey": NEWS_API_KEY,
                "pageSize": 6  # Increased to 6 articles
            }
        )
        
        if response.status_code != 200:
            raise Exception("Failed to fetch market news")
        
        news_data = response.json().get("articles", [])
        return [{
            "title": article["title"],
            "summary": article.get("description", "No description available"),
            "url": article["url"],
            "publishedAt": article.get("publishedAt", "")
        } for article in news_data]
        
    except Exception as e:
        print(f"Error fetching market news: {e}")
        return []

def generate_market_summary(sentiment, article_count):
    """Generate a market summary based on sentiment analysis"""
    if article_count == 0:
        return "Insufficient market data available for analysis."
    
    if sentiment > 0:
        return "Market sentiment is positive, suggesting favorable conditions for investment."
    elif sentiment < 0:
        return "Market sentiment is negative, suggesting caution in investment decisions."
    else:
        return "Market sentiment is neutral, suggesting stable but uncertain conditions."

def calculate_return(historical_data):
    """Calculate 30-day return from historical data"""
    if not historical_data or len(historical_data) < 2:
        return 0
    
    latest_price = historical_data[0]["price"]
    old_price = historical_data[-1]["price"]
    return ((latest_price - old_price) / old_price) * 100

def calculate_volatility(historical_data):
    """Calculate volatility from historical data"""
    if not historical_data or len(historical_data) < 2:
        return 0
    
    prices = [entry["price"] for entry in historical_data]
    returns = np.diff(prices) / prices[:-1]
    return np.std(returns) * np.sqrt(252) * 100

def determine_trend(historical_data):
    """Determine market trend from historical data"""
    if not historical_data or len(historical_data) < 2:
        return "Neutral"
    
    prices = [entry["price"] for entry in historical_data]
    if prices[0] > prices[-1] * 1.05:
        return "Upward"
    elif prices[0] < prices[-1] * 0.95:
        return "Downward"
    return "Sideways"

def determine_risk_level(volatility):
    """Determine risk level based on volatility"""
    if volatility > 25:
        return "High"
    elif volatility > 15:
        return "Moderate"
    return "Low"

def generate_technical_summary(stats):
    """Generate technical analysis summary"""
    summary_parts = []
    
    if stats["trend"] != "Neutral":
        summary_parts.append(f"Market showing {stats['trend'].lower()} trend")
    
    if stats["30_day_return"] > 5:
        summary_parts.append("Strong positive momentum")
    elif stats["30_day_return"] < -5:
        summary_parts.append("Significant market weakness")
    
    if not summary_parts:
        summary_parts.append("Market conditions are stable")
        
    return " | ".join(summary_parts)

def analyze_market_data(spy_data):
    """Analyze market data and generate statistics"""
    if not spy_data:
        return default_market_stats()

    try:
        stats = {
            "current_price": spy_data["current_price"],
            "30_day_return": calculate_return(spy_data["historical_data"]),
            "volatility": calculate_volatility(spy_data["historical_data"]),
            "trend": determine_trend(spy_data["historical_data"])
        }
        
        return {
            "market_stats": stats,
            "technical_analysis": {
                "summary": generate_technical_summary(stats),
                "risk_level": determine_risk_level(stats["volatility"])
            }
        }
    except Exception as e:
        print(f"Error in market data analysis: {e}")
        return default_market_stats()

def default_market_stats():
    """Return default market statistics when data is unavailable"""
    return {
        "market_stats": {
            "current_price": 0.0,
            "30_day_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "trend": "Neutral"
        },
        "technical_analysis": {
            "summary": "Market data currently unavailable. Please try again later.",
            "risk_level": "Moderate"
        }
    }

def analyze_news_sentiment(news_articles):
    """Analyze sentiment of news articles"""
    analysis = {
        "categorized_articles": {
            "positive": [],
            "neutral": [],
            "negative": []
        },
        "sentiment_stats": {
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "average": 0
        }
    }

    if not news_articles:
        return analysis

    total_sentiment = 0
    for article in news_articles:
        sentiment = TextBlob(article.get('summary', '')).sentiment.polarity
        
        if sentiment > 0.1:
            analysis["categorized_articles"]["positive"].append(article)
            analysis["sentiment_stats"]["positive_count"] += 1
        elif sentiment < -0.1:
            analysis["categorized_articles"]["negative"].append(article)
            analysis["sentiment_stats"]["negative_count"] += 1
        else:
            analysis["categorized_articles"]["neutral"].append(article)
            analysis["sentiment_stats"]["neutral_count"] += 1
            
        total_sentiment += sentiment

    total_articles = len(news_articles)
    if total_articles > 0:
        analysis["sentiment_stats"]["average"] = total_sentiment / total_articles

    analysis["market_outlook"] = {
        "outlook": "Bullish" if total_sentiment > 0 else "Bearish" if total_sentiment < 0 else "Neutral",
        "confidence": "High" if total_articles >= 5 else "Moderate" if total_articles >= 3 else "Low",
        "summary": generate_market_summary(total_sentiment, total_articles)
    }

    return analysis

if __name__ == '__main__':
    app.run(debug=True)