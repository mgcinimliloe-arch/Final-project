from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---- SQLite Database Setup ----
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trucking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---- Database Model ----
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # income, expense, adjustment_in, adjustment_out
    truck_id = db.Column(db.String(50))              # optional
    amount = db.Column(db.Float, nullable=False)
    expense_type = db.Column(db.String(50))         # optional
    note = db.Column(db.String(200))                # optional
    date = db.Column(db.DateTime, nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# ---- Helper Functions ----
def get_account_balance():
    balance = 0
    try:
        transactions = Transaction.query.all()
        for t in transactions:
            if t.type == "income":
                balance += t.amount
            elif t.type in ["expense", "adjustment_out"]:
                balance -= t.amount
            elif t.type == "adjustment_in":
                balance += t.amount
    except Exception as e:
        flash(f"Database error: {e}", "danger")
    return balance

# ---- Routes ----
@app.route("/", methods=["GET", "POST"])
def index():
    try:
        transactions = Transaction.query.order_by(Transaction.date).all()
        balance = get_account_balance()
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        transactions = []
        balance = 0

    if request.method == "POST":
        form_type = request.form.get("form_type")
        try:
            if form_type == "income":
                truck_id = request.form.get("truck_id", "")
                amount = float(request.form.get("amount", 0))
                note = request.form.get("note", "")

                if amount <= 0:
                    raise ValueError("Amount must be positive")

                t = Transaction(
                    type="income",
                    truck_id=truck_id,
                    amount=amount,
                    note=note,
                    date=datetime.now()
                )
                db.session.add(t)
                db.session.commit()
                flash("Income added successfully!", "success")

            elif form_type == "expense":
                truck_id = request.form.get("truck_id", "")
                amount = float(request.form.get("amount", 0))
                expense_type = request.form.get("expense_type", "")
                note = request.form.get("note", "")

                if amount <= 0:
                    raise ValueError("Amount must be positive")

                t = Transaction(
                    type="expense",
                    truck_id=truck_id,
                    amount=amount,
                    expense_type=expense_type,
                    note=note,
                    date=datetime.now()
                )
                db.session.add(t)
                db.session.commit()
                flash("Expense added successfully!", "success")

            elif form_type == "adjustment":
                amount = float(request.form.get("amount", 0))
                note = request.form.get("note", "")

                if amount == 0:
                    raise ValueError("Amount cannot be zero")

                adj_type = "adjustment_in" if amount > 0 else "adjustment_out"
                t = Transaction(
                    type=adj_type,
                    amount=abs(amount),
                    note=note,
                    date=datetime.now()
                )
                db.session.add(t)
                db.session.commit()
                flash("Balance adjusted successfully!", "success")

            else:
                flash("Unknown form submitted.", "danger")

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

        return redirect(url_for("index"))

    return render_template("index.html", balance=balance, history=transactions)

@app.route("/history/")
def history():
    try:
        transactions = Transaction.query.order_by(Transaction.date).all()

        # Optional filtering by line numbers
        line_from = request.args.get("line_from", type=int)
        line_to = request.args.get("line_to", type=int)
        if line_from is not None and line_to is not None:
            transactions = transactions[line_from:line_to]

    except Exception as e:
        flash(f"Database error: {e}", "danger")
        transactions = []

    return render_template("history.html", history=transactions)

# ---- Run App ----
if __name__ == "__main__":
    app.run(debug=True)
