# Stock Market Analysis Dashboard

A Flask-based web application for real-time stock market analysis with interactive visualizations and news integration.

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Run Locally](#run-locally)
- [API Reference](#api-reference)
- [Screenshots](#screenshots)
- [Demo](#demo)
- [Contributing](#contributing)
- [License](#license)

## Features

- Real-time stock price tracking
- Historical price data visualization
- Latest news articles integration
- Investment suggestions based on trends
- Interactive charts using Chart.js
- Responsive design

## Tech Stack

**Client:** HTML, CSS, JavaScript, Chart.js

**Server:** Python, Flask

## Installation

1. Clone the project

```bash
git clone https://github.com/yourusername/stock-analysis-dashboard.git
```

2. Go to the project directory
```bash
cd stock-analysis-dashboard
```

3. Create virtual environment
```bash
python -m venv venv
```

4. Activate virtual environment
```bash
venv\Scripts\activate
```


5. Install dependencies
```bash

pip install -r requirements.txt
```


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`NEWS_API_KEY` - Get from [News API](https://newsapi.org/)

`STOCKS_API_KEY` - Get from [Alpha Vantage](https://www.alphavantage.co/)

## Run Locally

Clone the project
```bash
git clone https://github.com/yourusername/stock-analysis-dashboard.git
```

Go to the project directory
```bash
cd stock-analysis-dashboard
```

# Install dependencies
```bash
pip install -r requirements.txt
```


## Start the server
``bash


python app.py
```

## API Reference

#### Get stock analysis
