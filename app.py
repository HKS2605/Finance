import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # get users stocks and shares
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    # get users cash balance
    cash = db.execute(
        "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
    )[0]["cash"]

    # initialize the total value variables
    total_value = cash
    grand_total = cash

    # iterate iver stocks
    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        stock["value"] = stock["price"] * stock["total_shares"]
        total_value += stock["value"]
        grand_total += stock["value"]

    return render_template(
        "index.html",
        stocks=stocks,
        cash=usd(cash),
        total_value=usd(total_value),
        grand_total=usd(grand_total),
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure symbol and no of shares is provided
        if not symbol:
            return apology("Must provide symbol")
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide positive integer number of shares")

        # lookup the provided symbol to check if it exists
        quote = lookup(symbol)
        if quote is None:
            return apology("Invalid Symbol")

        price = quote["price"]
        total_cost = int(shares) * price
        cash = db.execute(
            "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
        )[0]["cash"]

        # check if enough cash is avilabel
        if cash < total_cost:
            return apology("Not Enough cash")

        # update the users tabel
        db.execute(
            "UPDATE users SET cash = cash - :total_cost WHERE id = :user_id",
            total_cost=total_cost,
            user_id=session["user_id"],
        )

        # Update the Transaction History
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)",
            user_id=session["user_id"],
            symbol=symbol,
            shares=shares,
            price=price,
        )

        flash(f"Bought {shares} of {symbol} for {usd(total_cost)}")

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # query database for users transactions ordered by most recent transaction
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = :user_id ORDER BY timestamp DESC",
        user_id=session["user_id"],
    )

    # render history page with transactions
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        print("dfsadfsaf")
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote"""

    # When user gets there via post method
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)
        if not quote:
            return apology("Invalid Symbol", 400)
        return render_template("quote.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register New User"""
    # register new user
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password confirmation was submited
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)

        # Ensure Password is same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password doest match", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # check if username already exists
        if len(rows) != 0:
            return apology("username already exists", 400)

        # insert the username into the database
        db.execute(
            "INSERT INTO users (username, hash) VALUES(?, ?)",
            request.form.get("username"),
            generate_password_hash(request.form.get("password")),
        )

        # search for newly inserted user to assign sesssion id
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # remember which user has loged in
        session["user_od"] = rows[0]["id"]

        # redirect them to homepage
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # get users stocks and shares
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure symbol and no of shares is provided
        if not symbol:
            return apology("Must provide symbol")
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide positive integer number of shares")
        else:
            shares = int(shares)

        for stock in stocks:
            if stock["symbol"] == symbol:
                if stock["total_shares"] < shares:
                    return apology("not enough shares")
                else:
                    quote = lookup(symbol)
                    if quote is None:
                        return apology("Invalid Symbol")
                    price = quote["price"]
                    total_sale = shares * price

                    # update user table
                    db.execute(
                        "UPDATE users SET cash = cash + :total_sale WHERE id = :user_id",
                        total_sale=total_sale,
                        user_id=session["user_id"],
                    )

                    # add the sale to history
                    db.execute(
                        "INSERT INTO transactions (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)",
                        user_id=session["user_id"],
                        symbol=symbol,
                        shares=-shares,
                        price=price,
                    )

                    flash(f"Sold {shares} of {symbol} for {usd(total_sale)}")
                    return redirect("/")

        return apology("symbol not found")

    else:
        return render_template("sell.html", stocks=stocks)


@app.route("/password", methods=["GET", "POST"])
def password():
    """Change Password"""

    if request.method == "POST":
        # Ensure Old Password was submitted
        if not request.form.get("oldpassword"):
            return apology("must provide Old Password", 400)

        # Ensure password was submitted
        elif not request.form.get("newpassword"):
            return apology("must provide New password", 400)

        # Ensure Password is Not same
        elif request.form.get("oldpassword") == request.form.get("newpassword"):
            return apology("New password is Same as the Old Password", 400)

        newpassword = generate_password_hash(request.form.get("newpassword"))

        db.execute(
            "UPDATE users SET hash = :newpassword WHERE id = :user_id",
            newpassword=newpassword,
            user_id=session["user_id"],
        )

        flash("Password Changed")
        return redirect("/")
    else:
        return render_template("password.html")


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    """Allow admin to log in"""
    if request.method == "POST":
        # Get username and password from form
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if username and password fields are provided
        if not username or not password:
            return apology("Must provide username and password", 403)

        # Fetch admin credentials from the database
        admin = db.execute("SELECT * FROM admins WHERE username = ?", username)

        # Validate admin credentials
        if len(admin) != 1 or not check_password_hash(admin[0]["password_hash"], password):
            return apology("Invalid username and/or password", 403)

        # Remember admin login by setting a session
        session["admin_id"] = admin[0]["id"]
        print("adfdffdsfdf")
        # Redirect directly to admin dashboard
        return render_template("admin_dashboard.html")

    # If GET request, render the admin login page
    return render_template("admin_login.html")


@app.route("/admin_dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    """Admin dashboard for managing the application"""
    # if request.method == "POST":
    # Ensure the current user is an admin
    if "admin_id" not in session:
        return redirect("/admin_login")

    # 1. User Portfolio Report: Total shares owned by each user for different stocks
    user_portfolio = db.execute("SELECT user_id, symbol, SUM(shares) AS total_shares FROM transactions GROUP BY user_id, symbol HAVING total_shares > 0 ")

    # 2. User Transaction History: Full transaction history for all users
    user_transactions = db.execute("SELECT id, user_id, symbol, shares, price, timestamp FROM transactions ORDER BY timestamp DESC")

    # 3. Most Traded Stocks Report: Stocks with the highest number of trades
    most_traded_stocks = db.execute("SELECT symbol, COUNT(*) AS trade_count FROM transactions GROUP BY symbol ORDER BY trade_count DESC LIMIT 5 ")

    # 4. User Stock Holdings Report: Number of unique stocks owned by each user
    user_holdings = db.execute("SELECT user_id, COUNT(DISTINCT symbol) AS unique_stocks FROM transactions WHERE shares > 0 GROUP BY user_id")

    # 5. User Spending Report: Total amount spent by each user
    user_spending = db.execute("SELECT user_id, SUM(shares * price) AS total_spent FROM transactions WHERE shares > 0 GROUP BY user_id ORDER BY total_spent DESC ")

    # 6. Active Trading Users Report: Users with the most transactions
    active_users = db.execute("SELECT user_id, COUNT(*) AS transaction_count FROM transactions GROUP BY user_id ORDER BY transaction_count DESC LIMIT 5")

    # 7. Average Purchase Price per Stock: Average price users paid for each stock
    average_prices = db.execute(" SELECT symbol, AVG(price) AS average_price FROM transactions WHERE shares > 0 GROUP BY symbol")

    # 8. Stocks With Highest Profit/Loss Report: Stocks with the highest profit or loss
    profit_loss = db.execute(" SELECT symbol, SUM(shares * price) AS total_profit_loss FROM transactions GROUP BY symbol ORDER BY total_profit_loss DESC LIMIT 5")

    # 9. Profit and Loss Report: Overall profit or loss for each user and stock
    user_profit_loss = db.execute("SELECT user_id, symbol, SUM(shares * price) AS total_profit_loss FROM transactions GROUP BY user_id, symbol  ORDER BY user_id")

    # 10. Largest Single Transaction Report: Transaction with the highest value
    # largest_transaction = db.execute("""
    #     SELECT id, user_id, symbol, shares, price, (shares * price) AS total_value
    #     FROM transactions
    #     ORDER BY total_value DESC
    #     LIMIT 1
    # """)
    # largest_transaction = largest_transaction[0] if largest_transaction else None   # Fetch the first (and only) row

    # Fetch all users for the Manage Users section
    users = db.execute("SELECT id, username, cash FROM users")

    print(users)
    print(user_portfolio)
    print(average_prices)

    print("dfsfef")
    print("9456454")


    # Pass all data to the template
    return render_template("admin_dashboard.html",users=users, user_portfolio=user_portfolio, user_transactions=user_transactions, most_traded_stocks=most_traded_stocks, user_holdings=user_holdings, user_spending=user_spending, active_users=active_users, average_prices=average_prices, profit_loss=profit_loss, user_profit_loss=user_profit_loss )





