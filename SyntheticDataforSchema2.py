import sqlite3
import random
import datetime

DB_PATH = "ipeds_data.db"

def generate_stable_population_data(
    total_years=8,
    start_fall_year=2019,
    new_freshmen_each_fall=250,    # base number of new freshmen
    freshman_to_soph_prob=0.80,
    soph_to_junior_prob=0.85,
    junior_to_senior_prob=0.90,
    senior_grad_prob=0.70,
    race_penalty_for_retention=0.05,  # e.g. 5% penalty for Black students
    random_retention=False,
    base_dropout_prob=0.05,       # fallback dropout chance
    random_seed=42
):
    """
    Generates a multi-year 'stable-ish' population across multiple Fall terms.
    Key points:
      - Each 'Fall' term, we add new freshmen. The exact count is varied by ±20 randomly.
      - Each active student enrolls in some courses, we compute an average GPA for that term.
      - Retention for the next term depends on that GPA + a small penalty if they're Black.
      - Seniors can graduate, producing a row in 'completions' and leaving the system.
      - We store class_year, avg_gpa, and retained_next_term in the enrollments table.

    Make sure your DB schema includes 'class_year' and 'avg_gpa' columns in enrollments.
    """

    random.seed(random_seed)

    # 1) Connect to DB & enable foreign keys
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    # 2) Define our Fall terms
    term_labels = []
    current_year = start_fall_year
    for _ in range(total_years):
        term_labels.append(f"Fall {current_year}")
        current_year += 1

    # 3) Possibly insert some courses if not present
    possible_courses = [
        ("CSCI 101", "Intro to CS", 3),
        ("MATH 101", "College Algebra", 3),
        ("ENG 101",  "English Composition", 3),
        ("HIST 210", "World History", 3),
        ("BIO 110",  "General Biology", 4),
        ("PSYC 101", "Intro to Psychology", 3),
        ("ECON 101", "Principles of Econ", 3),
        ("CHEM 101", "General Chemistry", 4),
        ("PHYS 101", "General Physics", 4),
        ("PHIL 100", "Intro to Philosophy", 3)
    ]
    c.executemany("""
        INSERT OR IGNORE INTO courses(course_id, course_code, course_name, credit_hours)
        VALUES (?, ?, ?, ?);
    """, [
        (i+1, pc[0], pc[1], pc[2]) for i, pc in enumerate(possible_courses)
    ])
    conn.commit()

    # Build a dict: { course_id: (course_code, course_name, credit_hours) }
    course_dict = {}
    for i, (code, name, ch) in enumerate(possible_courses):
        course_id = i+1
        course_dict[course_id] = (code, name, ch)

    # 4) Weighted letter distribution & mapping
    letter_dist = [("A", 0.25), ("B", 0.35), ("C", 0.25), ("D", 0.10), ("F", 0.05)]
    letter_to_gpa = {"A":4.0, "B":3.0, "C":2.0, "D":1.0, "F":0.0}

    # We'll define a piecewise GPA->retention function
    def map_gpa_to_retention_prob(gpa):
        # e.g. 3.5+ => 0.90, 2.5+ => 0.75, 1.5+ => 0.55, 0.5+ => 0.35, else => 0.15
        if gpa >= 3.5:
            return 0.90
        elif gpa >= 2.5:
            return 0.75
        elif gpa >= 1.5:
            return 0.55
        elif gpa >= 0.5:
            return 0.35
        else:
            return 0.15

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
    for term_label in term_labels:
        # (A) Add new freshmen with random ±20 variation
        variation = random.randint(-20, 20)
        new_fresh_count = max(0, new_freshmen_each_fall + variation)

        for _ in range(new_fresh_count):
            sid = next_student_id
            next_student_id += 1

            # Random personal data
            genders = ["Male","Female"]
            gender = random.choice(genders)
            fname = random.choice(["John","Mike","David","Chris","James","Mary","Linda","Jennifer","Susan","Elizabeth"])
            lname = random.choice(["Smith","Jones","Brown","Johnson","Miller","Davis","Garcia","Taylor","Wilson","Hernandez"])
            race_cats = ["White","Black/African American","Hispanic/Latino","Asian","Two or More Races","Other/Unknown"]
            race = random.choice(race_cats)

            base_date = datetime.date(2025,1,7)
            age_days = random.randint(18*365, 22*365)
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
            program = random.choice(["11.0101","24.0101","52.0301","14.0901"])
            status = "Active"

            # Generate courses for this term
            num_courses = random.randint(2,5)
            course_ids = list(course_dict.keys())
            chosen_cids = random.sample(course_ids, num_courses)

            # We'll compute sum of (grade_points * credit_hrs) / sum(credit_hrs) for the GPA
            sum_gp = 0.0
            sum_credits = 0.0

            # Insert rows in course_enrollments
            enrollment_id = enrollment_id_counter
            for cid in chosen_cids:
                # pick a letter grade
                r = random.random()
                cum = 0.0
                letter_grade = "C"
                for (lg, p) in letter_dist:
                    cum += p
                    if r <= cum:
                        letter_grade = lg
                        break
                gp = letter_to_gpa[letter_grade]
                credit_hrs = course_dict[cid][2]

                sum_gp += (gp * credit_hrs)
                sum_credits += credit_hrs

                # record course enrollment
                course_enrollment_rows.append((
                    course_enroll_id_counter,
                    enrollment_id,
                    cid,
                    letter_grade,
                    gp
                ))
                course_enroll_id_counter += 1

            avg_gpa = sum_gp / sum_credits if sum_credits > 0 else 2.0

            # 1) Check if they're a senior => maybe graduate
            if s["class_year"] == 4:
                # chance to graduate
                if random.random() < senior_grad_prob:
                    # they graduate
                    s["active"] = False
                    status = "Completed"
                    # record a completion
                    completion_rows.append((
                        completion_id_counter,
                        s["student_id"],
                        random.choice(["Bachelor’s","Associate","Certificate <1 year"]),
                        program,
                        "2025-05-15"  # placeholder date
                    ))
                    completion_id_counter += 1

            # 2) If they're still active => apply retention logic
            retained_flag = 0
            if s["active"]:
                # map GPA -> base prob
                base_prob = map_gpa_to_retention_prob(avg_gpa)
                # Race penalty
                if s["race_eth"] == "Black/African American":
                    base_prob -= race_penalty_for_retention
                # clamp 0..1
                base_prob = max(0.0, min(1.0, base_prob))

                # random dropout check
                if random.random() < base_prob:
                    # they stay
                    retained_flag = 1
                    # also possibly advance class year if not senior
                    cy = s["class_year"]
                    if cy == 1 and random.random() < freshman_to_soph_prob:
                        s["class_year"] = 2
                    elif cy == 2 and random.random() < soph_to_junior_prob:
                        s["class_year"] = 3
                    elif cy == 3 and random.random() < junior_to_senior_prob:
                        s["class_year"] = 4
                else:
                    # dropout
                    s["active"] = False
                    status = "Withdrawn"

            # Now insert the enrollment row (with the final class_year after possible advancement)
            enrollment_rows.append((
                enrollment_id_counter,
                s["student_id"],
                term_label,
                program,
                status,
                retained_flag,           # retained_next_term
                s["class_year"],         # store the final class year for this term
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
