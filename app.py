from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "expense-tracker-secret"

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="expense_tracker"
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
            db.commit()
            flash("Registered successfully! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            cursor.close()
            db.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        else:
            flash("Wrong email or password!", "danger")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        title = request.form["title"]
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]
        cursor.execute("INSERT INTO expenses (user_id, title, amount, category, date) VALUES (%s, %s, %s, %s, %s)",
                       (session["user_id"], title, amount, category, date))
        db.commit()
        return redirect(url_for("dashboard"))

    # Filter
    filter_cat = request.args.get("category", "")
    if filter_cat and filter_cat != "All":
        cursor.execute("SELECT * FROM expenses WHERE user_id = %s AND category = %s ORDER BY date DESC", (session["user_id"], filter_cat))
        expenses = cursor.fetchall()
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s AND category = %s", (session["user_id"], filter_cat))
    else:
        cursor.execute("SELECT * FROM expenses WHERE user_id = %s ORDER BY date DESC", (session["user_id"],))
        expenses = cursor.fetchall()
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s", (session["user_id"],))
    total = cursor.fetchone()["total"] or 0
    # Get all categories for filter dropdown
    cursor.execute("SELECT DISTINCT category FROM expenses WHERE user_id = %s", (session["user_id"],))
    categories = [row["category"] for row in cursor.fetchall()]
    cursor.close()
    db.close()
    return render_template("dashboard.html", expenses=expenses, total=total, name=session.get("user_name"), categories=categories, filter_cat=filter_cat)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_expense(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        cursor.execute("UPDATE expenses SET title=%s, amount=%s, category=%s, date=%s WHERE id=%s AND user_id=%s",
                       (request.form["title"], request.form["amount"], request.form["category"], request.form["date"], id, session["user_id"]))
        db.commit()
        cursor.close(); db.close()
        return redirect(url_for("dashboard"))
    cursor.execute("SELECT * FROM expenses WHERE id=%s AND user_id=%s", (id, session["user_id"]))
    expense = cursor.fetchone()
    cursor.close(); db.close()
    return render_template("edit.html", e=expense)

@app.route("/delete/<int:id>")
def delete_expense(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = %s AND user_id = %s", (id, session["user_id"]))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("dashboard"))
def delete_expense(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = %s AND user_id = %s", (id, session["user_id"]))
    db.commit()
    cursor.close()
    db.close()
    flash("Expense deleted!", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)