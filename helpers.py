import csv
import datetime
import pytz
import yfinance as yf
import requests
import subprocess
import urllib
import uuid

from flask import redirect, render_template, session
from functools import wraps
from alpha_vantage.timeseries import TimeSeries


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol using Alpha Vantage API."""
    # Alpha Vantage API key
    API_KEY = "WWYUU0AQVWUWIT81"  # Your provided API key

    # Initialize Alpha Vantage TimeSeries object
    ts = TimeSeries(key=API_KEY, output_format="json")

    try:
        # Fetch the latest stock data using the "Quote Endpoint"
        data, meta_data = ts.get_quote_endpoint(symbol=symbol.upper())

        # Check if the data contains the required fields
        if "05. price" not in data:
            print(f"Error: No valid data found for symbol {symbol}")
            return None

        # Extract relevant fields
        price = float(data["05. price"])  # Latest stock price
        name = symbol.upper()  # Alpha Vantage doesn't return the company name

        # Return the stock data in the expected format
        return {
            "name": name,
            "price": round(price, 2),
            "symbol": symbol.upper()
        }

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    
    
# def lookup(symbol):
#     """Look up quote for symbol."""
    
#     # Prepare API request
#     symbol = symbol.upper()
#     end = datetime.datetime.now(pytz.timezone("US/Eastern"))
#     start = end - datetime.timedelta(days=7)
    
#     try:
#         # Fetch historical data for the symbol
#         stock = yf.Ticker(symbol)
#         hist = stock.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), interval="1d")

#         # Get the latest adjusted close price
#         if not hist.empty:
#             price = round(hist['Close'].iloc[-1], 2)
#             return {
#                 "name": symbol,
#                 "price": price,
#                 "symbol": symbol
#             }
#         else:
#             return None
#     except Exception as e:
#         print(f"Error: {e}")
#         return None

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
