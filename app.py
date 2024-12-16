from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
import os

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

if __name__ == '__main__':
    app.run(debug=True)