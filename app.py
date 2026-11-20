
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


# View all examinations
@app.route("/admin/examinations")
def admin_examinations():

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    examinations = conn.execute("""
        SELECT examinations.*, courses.course_name,
               courses.course_code
        FROM examinations
        JOIN courses
        ON examinations.course_id = courses.id
        ORDER BY examinations.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin/examinations.html",
        examinations=examinations
    )


# Add a new examination
@app.route("/admin/examinations/add", methods=["GET", "POST"])
def add_examination():

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    courses = conn.execute(
        "SELECT * FROM courses WHERE status = 'active'"
    ).fetchall()

    if request.method == "POST":

        course_id = request.form["course_id"]
        exam_name = request.form["exam_name"].strip()
        exam_type = request.form["exam_type"]
        duration = request.form["duration"]
        maximum_marks = request.form["maximum_marks"]

        slot_creation_start = request.form["slot_creation_start"]
        slot_creation_end = request.form["slot_creation_end"]
        booking_start = request.form["booking_start"]
        booking_end = request.form["booking_end"]

        status = request.form["status"]

        try:
            conn.execute("""
                INSERT INTO examinations
                (
                    course_id, exam_name, exam_type,
                    duration, maximum_marks,
                    slot_creation_start, slot_creation_end,
                    booking_start, booking_end, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                course_id,
                exam_name,
                exam_type,
                duration,
                maximum_marks,
                slot_creation_start,
                slot_creation_end,
                booking_start,
                booking_end,
                status
            ))

            conn.commit()
            flash("Examination added successfully.")

        except Exception:
            flash("Unable to add examination. Please check the details.")

        finally:
            conn.close()

        return redirect(url_for("admin_examinations"))

    conn.close()

    return render_template(
        "admin/examination_form.html",
        courses=courses,
        examination=None
    )


# Edit an examination
@app.route("/admin/examinations/edit/<int:exam_id>", methods=["GET", "POST"])
def edit_examination(exam_id):

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    examination = conn.execute(
        "SELECT * FROM examinations WHERE id = ?",
        (exam_id,)
    ).fetchone()

    courses = conn.execute(
        "SELECT * FROM courses"
    ).fetchall()

    if examination is None:
        conn.close()
        flash("Examination not found.")
        return redirect(url_for("admin_examinations"))

    if request.method == "POST":

        course_id = request.form["course_id"]
        exam_name = request.form["exam_name"].strip()
        exam_type = request.form["exam_type"]
        duration = request.form["duration"]
        maximum_marks = request.form["maximum_marks"]

        slot_creation_start = request.form["slot_creation_start"]
        slot_creation_end = request.form["slot_creation_end"]
        booking_start = request.form["booking_start"]
        booking_end = request.form["booking_end"]

        status = request.form["status"]

        try:
            conn.execute("""
                UPDATE examinations
                SET course_id = ?,
                    exam_name = ?,
                    exam_type = ?,
                    duration = ?,
                    maximum_marks = ?,
                    slot_creation_start = ?,
                    slot_creation_end = ?,
                    booking_start = ?,
                    booking_end = ?,
                    status = ?
                WHERE id = ?
            """, (
                course_id,
                exam_name,
                exam_type,
                duration,
                maximum_marks,
                slot_creation_start,
                slot_creation_end,
                booking_start,
                booking_end,
                status,
                exam_id
            ))

            conn.commit()
            flash("Examination updated successfully.")

        except Exception:
            flash("Unable to update examination.")

        finally:
            conn.close()

        return redirect(url_for("admin_examinations"))

    conn.close()

    return render_template(
        "admin/examination_form.html",
        courses=courses,
        examination=examination
    )


# Delete an examination
@app.route("/admin/examinations/delete/<int:exam_id>", methods=["POST"])
def delete_examination(exam_id):

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    try:
        conn.execute(
            "DELETE FROM examinations WHERE id = ?",
            (exam_id,)
        )

        conn.commit()
        flash("Examination deleted successfully.")

    except Exception:
        flash("This examination cannot be deleted because related records exist.")

    finally:
        conn.close()

    return redirect(url_for("admin_examinations"))


# View all rubrics
@app.route("/admin/rubrics")
def admin_rubrics():

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    rubrics = conn.execute("""
        SELECT rubrics.*, examinations.exam_name
        FROM rubrics
        JOIN examinations
        ON rubrics.examination_id = examinations.id
        ORDER BY rubrics.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin/rubrics.html",
        rubrics=rubrics
    )


# Add a rubric
@app.route("/admin/rubrics/add", methods=["GET", "POST"])
def add_rubric():

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    examinations = conn.execute(
        "SELECT * FROM examinations"
    ).fetchall()

    if request.method == "POST":

        examination_id = request.form["examination_id"]
        criterion_name = request.form["criterion_name"].strip()
        maximum_marks = request.form["maximum_marks"]
        weightage = request.form["weightage"]
        description = request.form["description"].strip()

        if not criterion_name:
            conn.close()
            flash("Criterion name is required.")
            return redirect(url_for("add_rubric"))

        try:
            maximum_marks = float(maximum_marks)
            weightage = float(weightage)

            if maximum_marks <= 0 or weightage < 0:
                raise ValueError

            conn.execute("""
                INSERT INTO rubrics
                (examination_id, criterion_name, maximum_marks,
                 weightage, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                examination_id,
                criterion_name,
                maximum_marks,
                weightage,
                description
            ))

            conn.commit()
            flash("Rubric added successfully.")

        except ValueError:
            flash("Enter valid marks and weightage.")

        except Exception:
            flash("Unable to add rubric.")

        finally:
            conn.close()

        return redirect(url_for("admin_rubrics"))

    conn.close()

    return render_template(
        "admin/rubric_form.html",
        examinations=examinations,
        rubric=None
    )


# Edit a rubric
@app.route("/admin/rubrics/edit/<int:rubric_id>", methods=["GET", "POST"])
def edit_rubric(rubric_id):

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    rubric = conn.execute(
        "SELECT * FROM rubrics WHERE id = ?",
        (rubric_id,)
    ).fetchone()

    examinations = conn.execute(
        "SELECT * FROM examinations"
    ).fetchall()

    if rubric is None:
        conn.close()
        flash("Rubric not found.")
        return redirect(url_for("admin_rubrics"))

    if request.method == "POST":

        examination_id = request.form["examination_id"]
        criterion_name = request.form["criterion_name"].strip()
        maximum_marks = request.form["maximum_marks"]
        weightage = request.form["weightage"]
        description = request.form["description"].strip()

        if not criterion_name:
            conn.close()
            flash("Criterion name is required.")
            return redirect(url_for("edit_rubric", rubric_id=rubric_id))

        try:
            maximum_marks = float(maximum_marks)
            weightage = float(weightage)

            if maximum_marks <= 0 or weightage < 0:
                raise ValueError

            conn.execute("""
                UPDATE rubrics
                SET examination_id = ?,
                    criterion_name = ?,
                    maximum_marks = ?,
                    weightage = ?,
                    description = ?
                WHERE id = ?
            """, (
                examination_id,
                criterion_name,
                maximum_marks,
                weightage,
                description,
                rubric_id
            ))

            conn.commit()
            flash("Rubric updated successfully.")

        except ValueError:
            flash("Enter valid marks and weightage.")

        except Exception:
            flash("Unable to update rubric.")

        finally:
            conn.close()

        return redirect(url_for("admin_rubrics"))

    conn.close()

    return render_template(
        "admin/rubric_form.html",
        examinations=examinations,
        rubric=rubric
    )


# Delete a rubric
@app.route("/admin/rubrics/delete/<int:rubric_id>", methods=["POST"])
def delete_rubric(rubric_id):

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    try:
        conn.execute(
            "DELETE FROM rubrics WHERE id = ?",
            (rubric_id,)
        )

        conn.commit()
        flash("Rubric deleted successfully.")

    except Exception:
        flash("This rubric cannot be deleted because it is used in an evaluation.")

    finally:
        conn.close()

    return redirect(url_for("admin_rubrics"))


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


# View all courses
@app.route("/admin/courses")
def admin_courses():

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    courses = conn.execute(
        "SELECT * FROM courses ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin/courses.html",
        courses=courses
    )


# Add a new course
@app.route("/admin/courses/add", methods=["GET", "POST"])
def add_course():

    if not is_admin():
        return redirect(url_for("login"))

    if request.method == "POST":

        course_code = request.form["course_code"].strip()
        course_name = request.form["course_name"].strip()
        description = request.form["description"].strip()

        if not course_code or not course_name:
            flash("Course code and course name are required.")
            return redirect(url_for("add_course"))

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO courses
                (course_code, course_name, description)
                VALUES (?, ?, ?)
            """, (course_code, course_name, description))

            conn.commit()
            flash("Course added successfully.")

        except Exception:
            flash("Course code already exists.")

        finally:
            conn.close()

        return redirect(url_for("admin_courses"))

    return render_template("admin/course_form.html", course=None)


# Edit an existing course
@app.route("/admin/courses/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    course = conn.execute(
        "SELECT * FROM courses WHERE id = ?",
        (course_id,)
    ).fetchone()

    if course is None:
        conn.close()
        flash("Course not found.")
        return redirect(url_for("admin_courses"))

    if request.method == "POST":

        course_code = request.form["course_code"].strip()
        course_name = request.form["course_name"].strip()
        description = request.form["description"].strip()

        if not course_code or not course_name:
            conn.close()
            flash("Course code and course name are required.")
            return redirect(url_for("edit_course", course_id=course_id))

        try:
            conn.execute("""
                UPDATE courses
                SET course_code = ?,
                    course_name = ?,
                    description = ?
                WHERE id = ?
            """, (
                course_code,
                course_name,
                description,
                course_id
            ))

            conn.commit()
            flash("Course updated successfully.")

        except Exception:
            flash("This course code is already being used.")

        finally:
            conn.close()

        return redirect(url_for("admin_courses"))

    conn.close()

    return render_template(
        "admin/course_form.html",
        course=course
    )


# Delete a course
@app.route("/admin/courses/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):

    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db_connection()

    try:
        conn.execute(
            "DELETE FROM courses WHERE id = ?",
            (course_id,)
        )

        conn.commit()
        flash("Course deleted successfully.")

    except Exception:
        flash("This course cannot be deleted because an examination is linked to it.")

    finally:
        conn.close()

    return redirect(url_for("admin_courses"))


# Logout
@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
