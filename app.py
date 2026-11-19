from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import create_database, get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "emp_secret_key_123"

# Database automatically create hogi
create_database()


@app.route("/")
def home():
    return render_template("home.html")


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        contact = request.form["contact"]
        department = request.form["department"]

        if role not in ["student", "examiner"]:
            flash("Please select a valid role.")
            return redirect(url_for("register"))

        conn = get_db_connection()

        try:
            if role == "examiner":
                status = "pending"
            else:
                status = "active"

            conn.execute("""
                INSERT INTO users
                (name, email, password, role, contact, department, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                email,
                generate_password_hash(password),
                role,
                contact,
                department,
                status
            ))

            conn.commit()

            if role == "examiner":
                flash("Registration successful. Wait for Admin approval.")
            else:
                flash("Registration successful. Please login.")

            return redirect(url_for("login"))

        except Exception:
            flash("This email is already registered.")

        finally:
            conn.close()

    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            if user["status"] == "pending":
                flash("Your examiner account is waiting for Admin approval.")
                return redirect(url_for("login"))

            if user["status"] != "active":
                flash("Your account is not active.")
                return redirect(url_for("login"))

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# Dashboard
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["name"],
        role=session["role"]
    )


# Logout
@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
