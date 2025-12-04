"""
IPEDS Fall Enrollment Database Schema Creator

This module creates a SQLite database with an IPEDS-like schema for storing
student enrollment data formatted for IPEDS Fall Enrollment reporting.

The database includes the following tables:
- students: Student demographic information with IPEDS categories
- enrollments: Term-level enrollment records with attendance/enrollment type
- courses: Course catalog
- course_enrollments: Individual course grades and enrollments
- completions: Degree/certificate completions
- cohorts: Prior year cohort data for retention calculations
- instructional_staff: Faculty data for student-to-faculty ratio
- state_fips: FIPS codes for state residence reporting

This schema supports IPEDS Fall Enrollment Parts A, B, C, E, and F.
"""

import sqlite3
import sys

# IPEDS Race/Ethnicity Categories (9 categories)
IPEDS_RACE_CATEGORIES = [
    "Hispanic/Latino",
    "American Indian/Alaska Native",
    "Asian",
    "Black/African American",
    "Native Hawaiian/Pacific Islander",
    "White",
    "Two or More Races",
    "Race/Ethnicity Unknown",
    "Nonresident Alien"
]

# State FIPS codes for Part C reporting
STATE_FIPS_CODES = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "DC": "11", "FL": "12",
    "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
    "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23",
    "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
    "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
    "WY": "56", "AS": "60", "GU": "66", "MP": "69", "PR": "72",
    "VI": "78", "FM": "64", "MH": "68", "PW": "70"
}


def create_ipeds_db_schema(db_path="ipeds_data.db"):
    """
    Creates the IPEDS Fall Enrollment database schema with all necessary tables.

    Creates tables supporting IPEDS Fall Enrollment Parts A, B, C, E, F:
    1. students: Core student demographics with IPEDS race/ethnicity categories
    2. enrollments: Term enrollment with attendance status, enrollment type
    3. courses: Course catalog with credit hours
    4. course_enrollments: Student grades in individual courses
    5. completions: Degrees/certificates awarded
    6. cohorts: Prior year cohort tracking for retention calculations
    7. instructional_staff: Faculty data for student-to-faculty ratio
    8. state_fips: FIPS code reference table

    Args:
        db_path: Path to the SQLite database file (default: "ipeds_data.db")

    Returns:
        None. Creates or updates the database file at db_path.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = ON;")

    # 1) students - Extended for IPEDS reporting
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        dob TEXT,                           -- Date of birth (YYYY-MM-DD)
        gender TEXT,                        -- Men/Women (IPEDS binary)
        race_ethnicity TEXT,                -- One of 9 IPEDS categories
        is_hispanic_latino INTEGER DEFAULT 0,  -- 1 if Hispanic/Latino
        citizenship_status TEXT,            -- US Citizen, Permanent Resident, Nonresident Alien
        state_of_residence TEXT,            -- State abbreviation
        state_fips_code TEXT,               -- FIPS code for state
        country_of_origin TEXT              -- For nonresident aliens
    );
    """)

    # 2) enrollments - Extended for IPEDS Fall Enrollment
    c.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY,
        student_id INTEGER,
        term TEXT,                          -- e.g., "Fall 2024"
        term_start_date TEXT,               -- ISO date format (YYYY-MM-DD)
        program TEXT,                       -- CIP code
        status TEXT,                        -- Active, Withdrawn, Completed
        retained_next_term INTEGER,         -- 0/1
        class_year INTEGER,                 -- 1=Fresh,2=Soph,3=Jr,4=Sr
        avg_gpa REAL,

        -- IPEDS-specific fields
        attendance_status TEXT,             -- Full-time, Part-time
        enrollment_type TEXT,               -- First-time, Transfer-in, Continuing
        level TEXT,                         -- Undergraduate, Graduate
        seeking_status TEXT,                -- Degree-seeking, Certificate-seeking, Non-degree-seeking
        degree_program_type TEXT,           -- Bachelor's, Associate, Certificate

        -- Distance Education (Part A)
        distance_education_status TEXT,     -- Exclusively DE, Some DE, No DE
        enrolled_in_state INTEGER,          -- 1 if enrolled in institution's state

        -- Credit hours for FT/PT determination
        credit_hours_attempted INTEGER,

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
        grade TEXT,                         -- e.g. A,B,C,D,F
        grade_points REAL,                  -- numeric scale (4.0 for A, etc.)
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id),
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    );
    """)

    # 5) completions
    c.execute("""
    CREATE TABLE IF NOT EXISTS completions (
        completion_id INTEGER PRIMARY KEY,
        student_id INTEGER,
        award_type TEXT,                    -- e.g. Bachelor's
        cip_code TEXT,                      -- e.g. "11.0101"
        completion_date TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );
    """)

    # 6) cohorts - For IPEDS Part E (Retention Rates)
    c.execute("""
    CREATE TABLE IF NOT EXISTS cohorts (
        cohort_id INTEGER PRIMARY KEY,
        student_id INTEGER,
        cohort_year INTEGER,                -- Year student entered (e.g., 2023)
        cohort_term TEXT,                   -- e.g., "Fall 2023"
        attendance_status TEXT,             -- Full-time, Part-time at entry
        enrollment_type TEXT,               -- First-time, Transfer-in
        seeking_status TEXT,                -- Degree-seeking, etc.

        -- Retention tracking
        is_excluded INTEGER DEFAULT 0,      -- 1 if excluded from cohort
        exclusion_reason TEXT,              -- Reason for exclusion if applicable
        retained_fall INTEGER,              -- 1 if enrolled in following fall
        completed_by_fall INTEGER,          -- 1 if completed program by following fall

        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );
    """)

    # 7) instructional_staff - For Part F (Student-to-Faculty Ratio)
    c.execute("""
    CREATE TABLE IF NOT EXISTS instructional_staff (
        staff_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        employment_status TEXT,             -- Full-time, Part-time
        faculty_status TEXT,                -- Tenured, Tenure-track, Non-tenure-track
        instructional_activity TEXT,        -- Teaching, Research, Both
        term TEXT,                          -- e.g., "Fall 2024"
        fte_value REAL,                     -- Full-time equivalent (1.0 = full-time)
        primary_function TEXT               -- Instruction, Research, Public Service
    );
    """)

    # 8) state_fips - Reference table for FIPS codes
    c.execute("""
    CREATE TABLE IF NOT EXISTS state_fips (
        state_abbr TEXT PRIMARY KEY,
        fips_code TEXT,
        state_name TEXT
    );
    """)

    # Populate state_fips table
    state_data = [
        ("AL", "01", "Alabama"), ("AK", "02", "Alaska"), ("AZ", "04", "Arizona"),
        ("AR", "05", "Arkansas"), ("CA", "06", "California"), ("CO", "08", "Colorado"),
        ("CT", "09", "Connecticut"), ("DE", "10", "Delaware"), ("DC", "11", "District of Columbia"),
        ("FL", "12", "Florida"), ("GA", "13", "Georgia"), ("HI", "15", "Hawaii"),
        ("ID", "16", "Idaho"), ("IL", "17", "Illinois"), ("IN", "18", "Indiana"),
        ("IA", "19", "Iowa"), ("KS", "20", "Kansas"), ("KY", "21", "Kentucky"),
        ("LA", "22", "Louisiana"), ("ME", "23", "Maine"), ("MD", "24", "Maryland"),
        ("MA", "25", "Massachusetts"), ("MI", "26", "Michigan"), ("MN", "27", "Minnesota"),
        ("MS", "28", "Mississippi"), ("MO", "29", "Missouri"), ("MT", "30", "Montana"),
        ("NE", "31", "Nebraska"), ("NV", "32", "Nevada"), ("NH", "33", "New Hampshire"),
        ("NJ", "34", "New Jersey"), ("NM", "35", "New Mexico"), ("NY", "36", "New York"),
        ("NC", "37", "North Carolina"), ("ND", "38", "North Dakota"), ("OH", "39", "Ohio"),
        ("OK", "40", "Oklahoma"), ("OR", "41", "Oregon"), ("PA", "42", "Pennsylvania"),
        ("RI", "44", "Rhode Island"), ("SC", "45", "South Carolina"), ("SD", "46", "South Dakota"),
        ("TN", "47", "Tennessee"), ("TX", "48", "Texas"), ("UT", "49", "Utah"),
        ("VT", "50", "Vermont"), ("VA", "51", "Virginia"), ("WA", "53", "Washington"),
        ("WV", "54", "West Virginia"), ("WI", "55", "Wisconsin"), ("WY", "56", "Wyoming"),
        ("AS", "60", "American Samoa"), ("GU", "66", "Guam"), ("MP", "69", "Northern Mariana Islands"),
        ("PR", "72", "Puerto Rico"), ("VI", "78", "Virgin Islands")
    ]

    c.executemany("""
        INSERT OR IGNORE INTO state_fips (state_abbr, fips_code, state_name)
        VALUES (?, ?, ?);
    """, state_data)

    conn.commit()
    conn.close()
    print(f"Database schema created or verified in '{db_path}'.")


if __name__ == "__main__":
    create_ipeds_db_schema()
