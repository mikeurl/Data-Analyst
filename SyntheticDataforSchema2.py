"""
Synthetic IPEDS Data Generator with GPA-Based Retention Modeling

This module generates realistic synthetic student data for an IPEDS-like database,
simulating multi-year student populations with:
- Realistic class progression (Freshman → Sophomore → Junior → Senior)
- GPA-based retention modeling
- Graduations and dropouts
- Course enrollments with grades
- Demographic diversity

IMPORTANT NOTE ON RETENTION MODELING:
The retention model includes a 'race_penalty_for_retention' parameter that can
simulate observed disparities in retention rates. This is included for research
and analysis purposes to model real-world patterns, NOT to perpetuate bias.
Users should understand that this creates synthetic data reflecting systemic
inequities that exist in higher education. Consider carefully whether including
this disparity serves your analysis goals.
"""

import sqlite3
import random
import datetime
import os
from typing import Dict, List, Tuple, Optional

# Use environment variable for DB path, with fallback to default
DB_PATH = os.getenv("IPEDS_DB_PATH", "ipeds_data.db")

###############################################################################
# CONSTANTS - Extracted magic numbers for configurability
###############################################################################

# Student age range (in years)
MIN_STUDENT_AGE = 18
MAX_STUDENT_AGE = 22

# Grade distribution (letter grade, probability)
DEFAULT_GRADE_DISTRIBUTION: List[Tuple[str, float]] = [
    ("A", 0.25),
    ("B", 0.35),
    ("C", 0.25),
    ("D", 0.10),
    ("F", 0.05),
]

# Grade to GPA mapping
GRADE_TO_GPA: Dict[str, float] = {
    "A": 4.0,
    "B": 3.0,
    "C": 2.0,
    "D": 1.0,
    "F": 0.0,
}

# GPA thresholds for retention probability
GPA_RETENTION_THRESHOLDS: List[Tuple[float, float]] = [
    (3.5, 0.90),  # GPA >= 3.5: 90% retention
    (2.5, 0.75),  # GPA >= 2.5: 75% retention
    (1.5, 0.55),  # GPA >= 1.5: 55% retention
    (0.5, 0.35),  # GPA >= 0.5: 35% retention
    (0.0, 0.15),  # GPA < 0.5: 15% retention
]

# Default GPA when no courses taken (should be rare)
DEFAULT_GPA = 2.0

# Freshman variation range
FRESHMAN_VARIATION = 20

# Available demographics
GENDERS = ["Male", "Female"]
RACE_CATEGORIES = [
    "White",
    "Black/African American",
    "Hispanic/Latino",
    "Asian",
    "Two or More Races",
    "Other/Unknown",
]
FIRST_NAMES = [
    "John", "Mike", "David", "Chris", "James",
    "Mary", "Linda", "Jennifer", "Susan", "Elizabeth",
]
LAST_NAMES = [
    "Smith", "Jones", "Brown", "Johnson", "Miller",
    "Davis", "Garcia", "Taylor", "Wilson", "Hernandez",
]
PROGRAMS = ["11.0101", "24.0101", "52.0301", "14.0901"]
AWARD_TYPES = ["Bachelor's", "Associate", "Certificate <1 year"]

# Course catalog
DEFAULT_COURSES: List[Tuple[str, str, int]] = [
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
    Generate multi-year student population data with realistic progression patterns.

    This function creates a synthetic student population over multiple Fall terms with:
    - New freshman cohorts each year (with ±FRESHMAN_VARIATION variation)
    - GPA-based retention modeling
    - Class year progression (Freshman → Sophomore → Junior → Senior)
    - Course enrollments with letter grades
    - Graduations and completions tracking

    Args:
        total_years: Number of Fall terms to simulate (default: 8)
        start_fall_year: Starting year for simulation (default: 2019)
        new_freshmen_each_fall: Base number of new freshmen per year (default: 250)
        freshman_to_soph_prob: Probability of freshman advancing (default: 0.80)
        soph_to_junior_prob: Probability of sophomore advancing (default: 0.85)
        junior_to_senior_prob: Probability of junior advancing (default: 0.90)
        senior_grad_prob: Probability of senior graduating (default: 0.70)
        race_penalty_for_retention: Retention penalty applied to certain demographics
                                    (default: 0.05). Set to 0 to remove disparity.
        base_dropout_prob: Fallback dropout probability (default: 0.05)
        random_seed: Random seed for reproducibility (default: 42)
        db_path: Path to the database (default: uses DB_PATH constant)

    Returns:
        None. Data is written directly to the SQLite database.

    Database Requirements:
        The enrollments table must include 'class_year' and 'avg_gpa' columns.
        Run create_ipeds_db_schema.py first to create the proper schema.
    """
    # Use provided db_path or fall back to module constant
    effective_db_path = db_path or DB_PATH

    random.seed(random_seed)

    # 1) Connect to DB & enable foreign keys
    conn = sqlite3.connect(effective_db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    # 2) Define our Fall terms
    term_labels = [f"Fall {start_fall_year + i}" for i in range(total_years)]

    # 3) Insert courses if not present
    c.executemany("""
        INSERT OR IGNORE INTO courses(course_id, course_code, course_name, credit_hours)
        VALUES (?, ?, ?, ?);
    """, [
        (i + 1, code, name, credits)
        for i, (code, name, credits) in enumerate(DEFAULT_COURSES)
    ])
    conn.commit()

    # Build a dict: { course_id: (course_code, course_name, credit_hours) }
    course_dict = {
        i + 1: (code, name, credits)
        for i, (code, name, credits) in enumerate(DEFAULT_COURSES)
    }

    def map_gpa_to_retention_prob(gpa: float) -> float:
        """Map GPA to retention probability using configured thresholds."""
        for threshold, prob in GPA_RETENTION_THRESHOLDS:
            if gpa >= threshold:
                return prob
        return GPA_RETENTION_THRESHOLDS[-1][1]  # Return lowest probability

    # We'll keep a list of all students in memory
    student_records = []
    next_student_id = 1

    # We'll store DB rows in lists, then do bulk inserts
    enrollment_rows = []
    course_enrollment_rows = []
    completion_rows = []

    # We'll track PK counters
    enrollment_id_counter = 1
    course_enroll_id_counter = 1
    completion_id_counter = 1

    # 5) For each fall term...
    for term_index, term_label in enumerate(term_labels):
        # (A) Add new freshmen with random variation
        variation = random.randint(-FRESHMAN_VARIATION, FRESHMAN_VARIATION)
        new_fresh_count = max(0, new_freshmen_each_fall + variation)

        # Calculate appropriate base date for this term
        term_year = start_fall_year + term_index
        base_date = datetime.date(term_year, 9, 1)  # Fall semester start

        for _ in range(new_fresh_count):
            sid = next_student_id
            next_student_id += 1

            # Random personal data using constants
            gender = random.choice(GENDERS)
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            race = random.choice(RACE_CATEGORIES)

            # Calculate DOB based on student age range
            age_days = random.randint(MIN_STUDENT_AGE * 365, MAX_STUDENT_AGE * 365)
            dob = base_date - datetime.timedelta(days=age_days)
            dob_str = dob.strftime("%Y-%m-%d")

            student_records.append({
                "student_id": sid,
                "first_name": fname,
                "last_name": lname,
                "dob": dob_str,
                "gender": gender,
                "race_eth": race,
                "class_year": 1,     # start as freshman
                "active": True
            })

        # (B) For each active student, generate courses, compute avg GPA, decide retention, grad
        updated_students = []
        for s in student_records:
            if not s["active"]:
                updated_students.append(s)
                continue

            # Program CIP code
            program = random.choice(PROGRAMS)
            status = "Active"

            # Generate courses for this term (2-5 courses)
            num_courses = random.randint(2, 5)
            course_ids = list(course_dict.keys())
            chosen_cids = random.sample(course_ids, min(num_courses, len(course_ids)))

            # Compute weighted GPA: sum(grade_points * credit_hrs) / sum(credit_hrs)
            sum_gp = 0.0
            sum_credits = 0.0

            # Insert rows in course_enrollments
            enrollment_id = enrollment_id_counter
            for cid in chosen_cids:
                # Pick a letter grade using weighted distribution
                r = random.random()
                cum = 0.0
                letter_grade = "C"  # default fallback
                for (lg, p) in DEFAULT_GRADE_DISTRIBUTION:
                    cum += p
                    if r <= cum:
                        letter_grade = lg
                        break

                gp = GRADE_TO_GPA[letter_grade]
                credit_hrs = course_dict[cid][2]

                sum_gp += (gp * credit_hrs)
                sum_credits += credit_hrs

                # Record course enrollment
                course_enrollment_rows.append((
                    course_enroll_id_counter,
                    enrollment_id,
                    cid,
                    letter_grade,
                    gp
                ))
                course_enroll_id_counter += 1

            # Calculate GPA with proper guard against division by zero
            if sum_credits > 0:
                avg_gpa = sum_gp / sum_credits
            else:
                # No courses taken (shouldn't happen with num_courses >= 2)
                avg_gpa = DEFAULT_GPA

            # Store the class year BEFORE any advancement for accurate enrollment record
            enrollment_class_year = s["class_year"]

            # 1) Check if they're a senior => maybe graduate
            if s["class_year"] == 4:
                if random.random() < senior_grad_prob:
                    # Student graduates
                    s["active"] = False
                    status = "Completed"
                    # Calculate completion date (May of the following year)
                    completion_date = datetime.date(term_year + 1, 5, 15)
                    completion_rows.append((
                        completion_id_counter,
                        s["student_id"],
                        random.choice(AWARD_TYPES),
                        program,
                        completion_date.strftime("%Y-%m-%d")
                    ))
                    completion_id_counter += 1

            # 2) If still active => apply retention logic
            # retained_next_term: 1 = student will return next term, 0 = student leaves
            retained_next_term = 0
            if s["active"]:
                # Calculate retention probability based on GPA
                retention_prob = map_gpa_to_retention_prob(avg_gpa)

                # Apply demographic-based retention penalty (models observed disparities)
                if s["race_eth"] == "Black/African American":
                    retention_prob -= race_penalty_for_retention

                # Clamp probability to valid range [0, 1]
                retention_prob = max(0.0, min(1.0, retention_prob))

                # Determine if student is retained for next term
                if random.random() < retention_prob:
                    # Student stays - will be retained for next term
                    retained_next_term = 1

                    # Check for class year advancement (only if not already senior)
                    cy = s["class_year"]
                    if cy == 1 and random.random() < freshman_to_soph_prob:
                        s["class_year"] = 2
                    elif cy == 2 and random.random() < soph_to_junior_prob:
                        s["class_year"] = 3
                    elif cy == 3 and random.random() < junior_to_senior_prob:
                        s["class_year"] = 4
                else:
                    # Student drops out
                    s["active"] = False
                    status = "Withdrawn"

            # Insert enrollment row with class year AT TIME OF ENROLLMENT
            # (not the advanced class year for next term)
            enrollment_rows.append((
                enrollment_id_counter,
                s["student_id"],
                term_label,
                program,
                status,
                retained_next_term,      # 1 if returning next term, 0 if leaving
                enrollment_class_year,   # class year during THIS enrollment
                avg_gpa
            ))
            enrollment_id_counter += 1

            updated_students.append(s)

        student_records = updated_students

    # 6) Bulk Insert all data
    # (A) Insert students
    student_data = []
    for s in student_records:
        student_data.append((
            s["student_id"],
            s["first_name"],
            s["last_name"],
            s["dob"],
            s["gender"],
            s["race_eth"]
        ))
    c.executemany("""
        INSERT OR IGNORE INTO students(student_id, first_name, last_name, dob, gender, race_ethnicity)
        VALUES (?, ?, ?, ?, ?, ?);
    """, student_data)

    # (B) Insert enrollments (with class_year + avg_gpa)
    c.executemany("""
        INSERT INTO enrollments(
            enrollment_id, 
            student_id, 
            term, 
            program, 
            status, 
            retained_next_term,
            class_year,
            avg_gpa
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, enrollment_rows)

    # (C) Insert course_enrollments
    c.executemany("""
        INSERT INTO course_enrollments(
            course_enrollment_id, 
            enrollment_id, 
            course_id, 
            grade, 
            grade_points
        ) VALUES (?, ?, ?, ?, ?);
    """, course_enrollment_rows)

    # (D) Insert completions
    c.executemany("""
        INSERT INTO completions(
            completion_id, 
            student_id, 
            award_type, 
            cip_code, 
            completion_date
        ) VALUES (?, ?, ?, ?, ?);
    """, completion_rows)

    conn.commit()
    conn.close()

    print(f"Done! Total unique students: {len(student_records)}")
    print(f"Enrollments inserted: {len(enrollment_rows)}")
    print(f"Course enrollments inserted: {len(course_enrollment_rows)}")
    print(f"Completions inserted: {len(completion_rows)}")


if __name__ == "__main__":
    generate_stable_population_data()
