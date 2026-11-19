import sqlite3 
import os
from werkzeug.security import generate_password_hash

DATABASE = os.path.join("instance", "emp.db") #Database file ka location path

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foregin_key = ON") # Foregin keys ko enable karta hai yeh 
    conn.row_factory = sqlite3.Row # row ko dictonary ki thara acces kar sakta hai

    return conn

def create_database():
    os.makedirs("instance", exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            contact TEXT,
            department TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

 # 2. Courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    # 3. Examinations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            exam_type TEXT NOT NULL,
            duration INTEGER NOT NULL,
            maximum_marks INTEGER NOT NULL,
            slot_creation_start TEXT,
            slot_creation_end TEXT,
            booking_start TEXT,
            booking_end TEXT,
            status TEXT DEFAULT 'draft',
            results_published INTEGER DEFAULT 0,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)

    # 4. Rubrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rubrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            examination_id INTEGER NOT NULL,
            criterion_name TEXT NOT NULL,
            maximum_marks REAL NOT NULL,
            weightage REAL DEFAULT 0,
            description TEXT,
            FOREIGN KEY (examination_id)
                REFERENCES examinations(id)
        )
    """)

    # 5. Slots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            examination_id INTEGER NOT NULL,
            examiner_id INTEGER NOT NULL,
            exam_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            maximum_capacity INTEGER NOT NULL,
            available_seats INTEGER NOT NULL,
            status TEXT DEFAULT 'available',
            FOREIGN KEY (examination_id)
                REFERENCES examinations(id),
            FOREIGN KEY (examiner_id)
                REFERENCES users(id)
        )
    """)

    # 6. Bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            examination_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'booked',
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (examination_id)
                REFERENCES examinations(id),
            FOREIGN KEY (slot_id) REFERENCES slots(id)
        )
    """)

    # Ek student ki ek examination mein
    # ek hi active booking allow hogi
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        unique_active_exam_booking
        ON bookings(student_id, examination_id)
        WHERE status = 'booked'
    """)

    # 7. Evaluations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER UNIQUE NOT NULL,
            examiner_id INTEGER NOT NULL,
            total_marks REAL DEFAULT 0,
            remarks TEXT,
            status TEXT DEFAULT 'pending',
            submitted_at TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (examiner_id) REFERENCES users(id)
        )
    """)

    # 8. Individual rubric scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluation_id INTEGER NOT NULL,
            rubric_id INTEGER NOT NULL,
            marks_obtained REAL NOT NULL,
            remarks TEXT,
            FOREIGN KEY (evaluation_id)
                REFERENCES evaluations(id),
            FOREIGN KEY (rubric_id)
                REFERENCES rubrics(id),
            UNIQUE(evaluation_id, rubric_id)
        )
    """)

    # Admin account automatically create karo
    admin = cursor.execute(
        "SELECT id FROM users WHERE role = 'admin'"
    ).fetchone()

    if admin is None:
        cursor.execute("""
            INSERT INTO users
            (name, email, password, role, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Administrator",
            "admin@emp.com",
            generate_password_hash("Admin@123"),
            "admin",
            "active"
        ))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")
