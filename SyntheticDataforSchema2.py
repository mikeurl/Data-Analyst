"""
Synthetic IPEDS Fall Enrollment Data Generator

This module generates realistic synthetic student data for IPEDS Fall Enrollment
reporting, including all fields required for Parts A, B, C, E, and F.

Generated data includes:
- Race/ethnicity (9 IPEDS categories)
- Gender (Men/Women)
- Attendance status (Full-time/Part-time)
- Enrollment type (First-time, Transfer-in, Continuing)
- Seeking status (Degree-seeking, Certificate-seeking, Non-degree-seeking)
- Age
- State of residence with FIPS codes
- Distance education status
- Prior year cohort data for retention calculations
- Instructional staff for student-to-faculty ratio

IMPORTANT NOTE ON RETENTION MODELING:
The retention model includes a 'race_penalty_for_retention' parameter that can
simulate observed disparities in retention rates. This is included for research
and analysis purposes to model real-world patterns, NOT to perpetuate bias.
"""

import sqlite3
import random
import datetime
import os
from typing import Dict, List, Tuple, Optional

# Use environment variable for DB path, with fallback to default
DB_PATH = os.getenv("IPEDS_DB_PATH", "ipeds_data.db")

###############################################################################
# CONSTANTS - IPEDS Categories and Demographics
###############################################################################

# IPEDS Race/Ethnicity Categories (9 categories) with distribution weights
IPEDS_RACE_CATEGORIES = [
    ("Hispanic/Latino", 0.18),
    ("American Indian/Alaska Native", 0.01),
    ("Asian", 0.07),
    ("Black/African American", 0.12),
    ("Native Hawaiian/Pacific Islander", 0.003),
    ("White", 0.52),
    ("Two or More Races", 0.04),
    ("Race/Ethnicity Unknown", 0.02),
    ("Nonresident Alien", 0.047)
]

# Gender distribution (IPEDS binary)
GENDERS = [("Men", 0.45), ("Women", 0.55)]

# Enrollment type probabilities for first-time students
ENROLLMENT_TYPES = [
    ("First-time", 0.60),
    ("Transfer-in", 0.25),
    ("Continuing", 0.15)
]

# Attendance status with credit hour ranges
ATTENDANCE_STATUS = [
    ("Full-time", 0.70),  # 12+ credit hours
    ("Part-time", 0.30)   # < 12 credit hours
]

# Degree seeking status
SEEKING_STATUS = [
    ("Degree-seeking", 0.85),
    ("Certificate-seeking", 0.10),
    ("Non-degree-seeking", 0.05)
]

# Distance education status
DISTANCE_ED_STATUS = [
    ("No DE", 0.50),
    ("Some DE", 0.35),
    ("Exclusively DE", 0.15)
]

# State distribution (simplified - top 10 states with weights)
STATE_DISTRIBUTION = [
    ("IN", 0.40),  # Home state
    ("IL", 0.12),
    ("OH", 0.10),
    ("MI", 0.08),
    ("KY", 0.05),
    ("CA", 0.04),
    ("TX", 0.04),
    ("NY", 0.03),
    ("FL", 0.03),
    ("PA", 0.02),
    # Remainder distributed across other states
]

# All US states for random distribution
ALL_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
    "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
    "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

# FIPS codes
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "DC": "11", "FL": "12",
    "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
    "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23",
    "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
    "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56"
}

# Countries for nonresident aliens
COUNTRIES = [
    "China", "India", "South Korea", "Saudi Arabia", "Canada",
    "Vietnam", "Taiwan", "Japan", "Brazil", "Mexico",
    "Nigeria", "Nepal", "Iran", "United Kingdom", "Germany"
]

# Student age ranges by enrollment type
AGE_RANGES = {
    "First-time": (17, 20),
    "Transfer-in": (19, 25),
    "Continuing": (18, 30)
}

# Age categories for Part B
AGE_CATEGORIES = [
    "Under 18",
    "18-19",
    "20-21",
    "22-24",
    "25-29",
    "30-34",
    "35-39",
    "40-49",
    "50-64",
    "65 and over",
    "Age unknown"
]

# Grade distribution
DEFAULT_GRADE_DISTRIBUTION: List[Tuple[str, float]] = [
    ("A", 0.25),
    ("B", 0.35),
    ("C", 0.25),
    ("D", 0.10),
    ("F", 0.05),
]

GRADE_TO_GPA: Dict[str, float] = {
    "A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0
}

# GPA thresholds for retention
GPA_RETENTION_THRESHOLDS = [
    (3.5, 0.90), (2.5, 0.75), (1.5, 0.55), (0.5, 0.35), (0.0, 0.15)
]

# Name pools
FIRST_NAMES = [
    "James", "Michael", "Robert", "David", "William", "John", "Richard",
    "Joseph", "Thomas", "Christopher", "Charles", "Daniel", "Matthew",
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Margaret"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
]

# CIP codes for programs
PROGRAMS = ["11.0101", "24.0101", "52.0301", "14.0901", "26.0101"]
AWARD_TYPES = ["Bachelor's", "Associate", "Certificate"]

# Course catalog
DEFAULT_COURSES = [
    ("CSCI 101", "Intro to CS", 3),
    ("MATH 101", "College Algebra", 3),
    ("ENG 101", "English Composition", 3),
    ("HIST 210", "World History", 3),
    ("BIO 110", "General Biology", 4),
    ("PSYC 101", "Intro to Psychology", 3),
    ("ECON 101", "Principles of Econ", 3),
    ("CHEM 101", "General Chemistry", 4),
    ("PHYS 101", "General Physics", 4),
    ("PHIL 100", "Intro to Philosophy", 3),
]

# Instructional staff data
FACULTY_FIRST_NAMES = [
    "Robert", "William", "Richard", "James", "Thomas", "Michael",
    "Patricia", "Elizabeth", "Susan", "Margaret", "Dorothy", "Helen"
]

FACULTY_LAST_NAMES = [
    "Anderson", "Thompson", "White", "Harris", "Clark", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright"
]


###############################################################################
# HELPER FUNCTIONS
###############################################################################

def weighted_choice(choices: List[Tuple[str, float]]) -> str:
    """Select from weighted choices."""
    r = random.random()
    cum = 0.0
    for item, weight in choices:
        cum += weight
        if r <= cum:
            return item
    return choices[-1][0]


def get_state_of_residence() -> str:
    """Get a state with realistic distribution."""
    r = random.random()
    cum = 0.0
    for state, weight in STATE_DISTRIBUTION:
        cum += weight
        if r <= cum:
            return state
    # Remainder: random from all states
    return random.choice(ALL_STATES)


def calculate_age_as_of_date(dob: datetime.date, as_of: datetime.date) -> int:
    """Calculate age in years as of a specific date."""
    age = as_of.year - dob.year
    if (as_of.month, as_of.day) < (dob.month, dob.day):
        age -= 1
    return age


def get_age_category(age: int) -> str:
    """Map age to IPEDS age category."""
    if age < 18:
        return "Under 18"
    elif age <= 19:
        return "18-19"
    elif age <= 21:
        return "20-21"
    elif age <= 24:
        return "22-24"
    elif age <= 29:
        return "25-29"
    elif age <= 34:
        return "30-34"
    elif age <= 39:
        return "35-39"
    elif age <= 49:
        return "40-49"
    elif age <= 64:
        return "50-64"
    else:
        return "65 and over"


def map_gpa_to_retention_prob(gpa: float) -> float:
    """Map GPA to retention probability."""
    for threshold, prob in GPA_RETENTION_THRESHOLDS:
        if gpa >= threshold:
            return prob
    return GPA_RETENTION_THRESHOLDS[-1][1]


###############################################################################
# MAIN DATA GENERATION FUNCTION
###############################################################################

def generate_stable_population_data(
    total_years: int = 8,
    start_fall_year: int = 2019,
    new_freshmen_each_fall: int = 250,
    freshman_to_soph_prob: float = 0.80,
    soph_to_junior_prob: float = 0.85,
    junior_to_senior_prob: float = 0.90,
    senior_grad_prob: float = 0.70,
    race_penalty_for_retention: float = 0.05,
    base_dropout_prob: float = 0.05,
    random_seed: int = 42,
    db_path: Optional[str] = None,
) -> None:
    """
    Generate multi-year IPEDS-compliant student population data.

    Creates synthetic data supporting IPEDS Fall Enrollment Parts A, B, C, E, F.
    """
    effective_db_path = db_path or DB_PATH
    random.seed(random_seed)

    conn = sqlite3.connect(effective_db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    # Define Fall terms
    term_labels = [f"Fall {start_fall_year + i}" for i in range(total_years)]

    # Insert courses
    c.executemany("""
        INSERT OR IGNORE INTO courses(course_id, course_code, course_name, credit_hours)
        VALUES (?, ?, ?, ?);
    """, [(i + 1, code, name, credits) for i, (code, name, credits) in enumerate(DEFAULT_COURSES)])
    conn.commit()

    course_dict = {i + 1: (code, name, credits) for i, (code, name, credits) in enumerate(DEFAULT_COURSES)}

    # Storage for records
    student_records = []
    next_student_id = 1
    enrollment_rows = []
    course_enrollment_rows = []
    completion_rows = []
    cohort_rows = []
    enrollment_id_counter = 1
    course_enroll_id_counter = 1
    completion_id_counter = 1
    cohort_id_counter = 1

    # Institution's home state (for in-state enrollment)
    INSTITUTION_STATE = "IN"

    # Track first-time students for cohort tracking
    first_time_students = {}

    for term_index, term_label in enumerate(term_labels):
        term_year = start_fall_year + term_index
        base_date = datetime.date(term_year, 9, 1)
        term_start_date = f"{term_year}-09-01"

        # Add new students
        variation = random.randint(-20, 20)
        new_student_count = max(0, new_freshmen_each_fall + variation)

        for _ in range(new_student_count):
            sid = next_student_id
            next_student_id += 1

            # Demographics
            gender = weighted_choice(GENDERS)
            race = weighted_choice(IPEDS_RACE_CATEGORIES)
            enrollment_type = weighted_choice(ENROLLMENT_TYPES)

            # Age based on enrollment type
            min_age, max_age = AGE_RANGES[enrollment_type]
            age_days = random.randint(min_age * 365, max_age * 365)
            dob = base_date - datetime.timedelta(days=age_days)
            dob_str = dob.strftime("%Y-%m-%d")

            # State of residence
            if race == "Nonresident Alien":
                state_of_residence = None
                state_fips = None
                citizenship = "Nonresident Alien"
                country = random.choice(COUNTRIES)
                is_hispanic = 0
            else:
                state_of_residence = get_state_of_residence()
                state_fips = STATE_FIPS.get(state_of_residence)
                citizenship = random.choice(["US Citizen", "Permanent Resident"])
                country = "United States"
                is_hispanic = 1 if race == "Hispanic/Latino" else 0

            student_records.append({
                "student_id": sid,
                "first_name": random.choice(FIRST_NAMES),
                "last_name": random.choice(LAST_NAMES),
                "dob": dob_str,
                "gender": gender,
                "race_ethnicity": race,
                "is_hispanic_latino": is_hispanic,
                "citizenship_status": citizenship,
                "state_of_residence": state_of_residence,
                "state_fips_code": state_fips,
                "country_of_origin": country,
                "class_year": 1 if enrollment_type == "First-time" else random.randint(1, 3),
                "active": True,
                "enrollment_type": enrollment_type,
                "first_term": term_label
            })

            # Track first-time students for cohort
            if enrollment_type == "First-time":
                first_time_students[sid] = {
                    "cohort_year": term_year,
                    "cohort_term": term_label
                }

        # Process all active students
        updated_students = []
        for s in student_records:
            if not s["active"]:
                updated_students.append(s)
                continue

            # Determine if this is their first term
            is_first_term = s.get("first_term") == term_label
            enrollment_type = s["enrollment_type"] if is_first_term else "Continuing"

            # Attendance status and credit hours
            attendance_status = weighted_choice(ATTENDANCE_STATUS)
            if attendance_status == "Full-time":
                credit_hours = random.randint(12, 18)
            else:
                credit_hours = random.randint(3, 11)

            # Seeking status
            seeking_status = weighted_choice(SEEKING_STATUS)

            # Distance education
            distance_ed = weighted_choice(DISTANCE_ED_STATUS)

            # In-state enrollment
            enrolled_in_state = 1 if s.get("state_of_residence") == INSTITUTION_STATE else 0

            # Program and status
            program = random.choice(PROGRAMS)
            status = "Active"

            # Generate courses
            num_courses = random.randint(2, 5)
            chosen_cids = random.sample(list(course_dict.keys()), min(num_courses, len(course_dict)))

            sum_gp = 0.0
            sum_credits = 0.0
            enrollment_id = enrollment_id_counter

            for cid in chosen_cids:
                letter_grade = weighted_choice(DEFAULT_GRADE_DISTRIBUTION)
                gp = GRADE_TO_GPA[letter_grade]
                credit_hrs = course_dict[cid][2]
                sum_gp += gp * credit_hrs
                sum_credits += credit_hrs

                course_enrollment_rows.append((
                    course_enroll_id_counter, enrollment_id, cid, letter_grade, gp
                ))
                course_enroll_id_counter += 1

            avg_gpa = sum_gp / sum_credits if sum_credits > 0 else 2.0
            enrollment_class_year = s["class_year"]

            # Graduation check for seniors
            if s["class_year"] == 4 and random.random() < senior_grad_prob:
                s["active"] = False
                status = "Completed"
                completion_date = datetime.date(term_year + 1, 5, 15)
                completion_rows.append((
                    completion_id_counter, s["student_id"],
                    random.choice(AWARD_TYPES), program,
                    completion_date.strftime("%Y-%m-%d")
                ))
                completion_id_counter += 1

            # Retention logic
            retained_next_term = 0
            if s["active"]:
                retention_prob = map_gpa_to_retention_prob(avg_gpa)
                if s["race_ethnicity"] == "Black/African American":
                    retention_prob -= race_penalty_for_retention
                retention_prob = max(0.0, min(1.0, retention_prob))

                if random.random() < retention_prob:
                    retained_next_term = 1
                    cy = s["class_year"]
                    if cy == 1 and random.random() < freshman_to_soph_prob:
                        s["class_year"] = 2
                    elif cy == 2 and random.random() < soph_to_junior_prob:
                        s["class_year"] = 3
                    elif cy == 3 and random.random() < junior_to_senior_prob:
                        s["class_year"] = 4
                else:
                    s["active"] = False
                    status = "Withdrawn"

            # Insert enrollment with all IPEDS fields
            enrollment_rows.append((
                enrollment_id_counter,
                s["student_id"],
                term_label,
                term_start_date,
                program,
                status,
                retained_next_term,
                enrollment_class_year,
                avg_gpa,
                attendance_status,
                enrollment_type,
                "Undergraduate",
                seeking_status,
                "Bachelor's" if seeking_status == "Degree-seeking" else "Certificate",
                distance_ed,
                enrolled_in_state,
                credit_hours
            ))
            enrollment_id_counter += 1

            updated_students.append(s)

        student_records = updated_students

    # Create cohort records for retention tracking (Part E)
    for sid, cohort_info in first_time_students.items():
        student = next((s for s in student_records if s["student_id"] == sid), None)
        if not student:
            continue

        # Find their first enrollment
        first_enrollment = next(
            (e for e in enrollment_rows if e[1] == sid and e[2] == cohort_info["cohort_term"]),
            None
        )
        if not first_enrollment:
            continue

        attendance = first_enrollment[9]  # attendance_status
        seeking = first_enrollment[11]     # seeking_status

        # Check if retained to following fall
        following_fall = f"Fall {cohort_info['cohort_year'] + 1}"
        retained = any(e[1] == sid and e[2] == following_fall for e in enrollment_rows)
        completed = any(c[1] == sid for c in completion_rows)

        # Exclusion (e.g., deceased, military, etc.) - small random chance
        is_excluded = 1 if random.random() < 0.02 else 0
        exclusion_reason = "Deceased or permanent disability" if is_excluded else None

        cohort_rows.append((
            cohort_id_counter,
            sid,
            cohort_info["cohort_year"],
            cohort_info["cohort_term"],
            attendance,
            "First-time",
            seeking,
            is_excluded,
            exclusion_reason,
            1 if retained else 0,
            1 if completed else 0
        ))
        cohort_id_counter += 1

    # Bulk insert students with extended fields
    student_data = [
        (s["student_id"], s["first_name"], s["last_name"], s["dob"],
         s["gender"], s["race_ethnicity"], s["is_hispanic_latino"],
         s["citizenship_status"], s["state_of_residence"],
         s["state_fips_code"], s["country_of_origin"])
        for s in student_records
    ]
    c.executemany("""
        INSERT OR IGNORE INTO students(
            student_id, first_name, last_name, dob, gender, race_ethnicity,
            is_hispanic_latino, citizenship_status, state_of_residence,
            state_fips_code, country_of_origin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, student_data)

    # Insert enrollments with all IPEDS fields
    c.executemany("""
        INSERT INTO enrollments(
            enrollment_id, student_id, term, term_start_date, program, status,
            retained_next_term, class_year, avg_gpa, attendance_status,
            enrollment_type, level, seeking_status, degree_program_type,
            distance_education_status, enrolled_in_state, credit_hours_attempted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, enrollment_rows)

    # Insert course enrollments
    c.executemany("""
        INSERT INTO course_enrollments(
            course_enrollment_id, enrollment_id, course_id, grade, grade_points
        ) VALUES (?, ?, ?, ?, ?);
    """, course_enrollment_rows)

    # Insert completions
    c.executemany("""
        INSERT INTO completions(
            completion_id, student_id, award_type, cip_code, completion_date
        ) VALUES (?, ?, ?, ?, ?);
    """, completion_rows)

    # Insert cohorts
    c.executemany("""
        INSERT INTO cohorts(
            cohort_id, student_id, cohort_year, cohort_term, attendance_status,
            enrollment_type, seeking_status, is_excluded, exclusion_reason,
            retained_fall, completed_by_fall
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, cohort_rows)

    # Generate instructional staff for Part F
    staff_rows = []
    staff_id = 1
    num_faculty = max(20, len(student_records) // 15)  # Rough 15:1 ratio

    for _ in range(num_faculty):
        employment = random.choice(["Full-time", "Part-time"])
        fte = 1.0 if employment == "Full-time" else random.uniform(0.25, 0.75)
        faculty_status = random.choice(["Tenured", "Tenure-track", "Non-tenure-track"])

        for term in term_labels:
            staff_rows.append((
                staff_id,
                random.choice(FACULTY_FIRST_NAMES),
                random.choice(FACULTY_LAST_NAMES),
                employment,
                faculty_status,
                "Teaching",
                term,
                fte,
                "Instruction"
            ))
        staff_id += 1

    c.executemany("""
        INSERT OR IGNORE INTO instructional_staff(
            staff_id, first_name, last_name, employment_status, faculty_status,
            instructional_activity, term, fte_value, primary_function
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, staff_rows)

    conn.commit()
    conn.close()

    print(f"Done! Total unique students: {len(student_records)}")
    print(f"Enrollments inserted: {len(enrollment_rows)}")
    print(f"Course enrollments inserted: {len(course_enrollment_rows)}")
    print(f"Completions inserted: {len(completion_rows)}")
    print(f"Cohort records inserted: {len(cohort_rows)}")
    print(f"Staff records inserted: {len(staff_rows)}")


if __name__ == "__main__":
    generate_stable_population_data()
