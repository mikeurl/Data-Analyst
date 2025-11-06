"""
IPEDS Database Schema Creator

This module creates a SQLite database with an IPEDS-like schema for storing
student enrollment, course, and completion data.

The database includes the following tables:
- students: Student demographic information
- enrollments: Term-level enrollment records with retention tracking
- courses: Course catalog
- course_enrollments: Individual course grades and enrollments
- completions: Degree/certificate completions

This schema is designed to support analysis of:
- Student retention and progression
- Academic performance (GPA tracking)
- Completion rates by program
- Demographic equity analyses
"""

import sqlite3
import sys

def create_ipeds_db_schema(db_path="ipeds_data.db"):
    """
    Creates the IPEDS-like database schema with all necessary tables.

    Creates five related tables:
    1. students: Core student demographics (race/ethnicity, gender, DOB)
    2. enrollments: Term enrollment records with class_year, GPA, and retention flag
    3. courses: Course catalog with credit hours
    4. course_enrollments: Student grades in individual courses
    5. completions: Degrees/certificates awarded

    Args:
        db_path: Path to the SQLite database file (default: "ipeds_data.db")

    Returns:
        None. Creates or updates the database file at db_path.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = ON;")

    # 1) students
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        dob TEXT,
        gender TEXT,
        race_ethnicity TEXT
    );
    """)

    # 2) enrollments
    #    includes class_year and avg_gpa
    c.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY,
        student_id INTEGER,
        term TEXT,
        program TEXT,
        status TEXT,
        retained_next_term INTEGER,   -- 0/1
        class_year INTEGER,           -- 1=Fresh,2=Soph,3=Jr,4=Sr
        avg_gpa REAL,                 -- store the computed term GPA
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );
    """)

    # 3) courses
    c.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY,
        course_code TEXT,
        course_name TEXT,
        credit_hours INTEGER
    );
    """)

    # 4) course_enrollments
    c.execute("""
    CREATE TABLE IF NOT EXISTS course_enrollments (
        course_enrollment_id INTEGER PRIMARY KEY,
        enrollment_id INTEGER,
        course_id INTEGER,
        grade TEXT,          -- e.g. A,B,C,D,F
        grade_points REAL,   -- numeric scale (4.0 for A, etc.)
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id),
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    );
    """)

    # 5) completions
    c.execute("""
    CREATE TABLE IF NOT EXISTS completions (
        completion_id INTEGER PRIMARY KEY,
        student_id INTEGER,
        award_type TEXT,    -- e.g. Bachelor's
        cip_code TEXT,      -- e.g. "11.0101"
        completion_date TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database schema created or verified in '{db_path}'.")

if __name__ == "__main__":
    create_ipeds_db_schema()
