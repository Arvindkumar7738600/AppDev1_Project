
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import create_database, get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "emp_secret_key_123"

create_database()


@app.route("/")
def home():
    return render_template("home.html")


# Check whether the logged-in user is Admin
def is_admin():
    return "user_id" in session and session.get("role") == "admin"


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

        if not name.strip() or not password:
            flash("Name and password are required.")
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


# Send users to their correct dashboard
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "dashboard.html",
        name=session["name"],
        role=session["role"]
    )


# Admin Dashboard
@app.route("/admin/dashboard")
def admin_dashboard():

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    total_courses = conn.execute(
        "SELECT COUNT(*) FROM courses"
    ).fetchone()[0]

    total_examinations = conn.execute(
        "SELECT COUNT(*) FROM examinations"
    ).fetchone()[0]

    total_examiners = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'examiner'"
    ).fetchone()[0]

    total_students = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'student'"
    ).fetchone()[0]

    total_slots = conn.execute(
        "SELECT COUNT(*) FROM slots"
    ).fetchone()[0]

    total_bookings = conn.execute(
        "SELECT COUNT(*) FROM bookings"
    ).fetchone()[0]

    pending_examiners = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'examiner' AND status = 'pending'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_courses=total_courses,
        total_examinations=total_examinations,
        total_examiners=total_examiners,
        total_students=total_students,
        total_slots=total_slots,
        total_bookings=total_bookings,
        pending_examiners=pending_examiners
    )


# Show examiner registration requests
@app.route("/admin/examiners")
def admin_examiners():

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    examiners = conn.execute("""
        SELECT * FROM users
        WHERE role = 'examiner'
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin/examiners.html",
        examiners=examiners
    )


# Approve an examiner
@app.route("/admin/approve-examiner/<int:examiner_id>", methods=["POST"])
def approve_examiner(examiner_id):

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    conn.execute("""
        UPDATE users
        SET status = 'active'
        WHERE id = ? AND role = 'examiner'
    """, (examiner_id,))

    conn.commit()
    conn.close()

    flash("Examiner approved successfully.")

    return redirect(url_for("admin_examiners"))


# Logout
@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
