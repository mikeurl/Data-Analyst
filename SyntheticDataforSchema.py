import sqlite3
import random
import datetime

DB_PATH = "ipeds_data.db"

def generate_stable_population_data(
    total_years=8,
    start_fall_year=2019,
    new_freshmen_each_fall=250,
    freshman_to_soph_prob=0.80,
    soph_to_junior_prob=0.85,
    junior_to_senior_prob=0.90,
    senior_grad_prob=0.70,
    race_penalty_for_retention=0.05,
    base_dropout_prob=0.05,
    random_seed=42
):
    """
    Generates a multi-year stable-ish population for a sequence of Fall terms.
    Each year:
      - We add new freshmen.
      - Existing students may drop out, advance in class year, or graduate (if senior).
      - We create 'enrollments' + course_enrollments for active students.
      - Some seniors graduate, producing rows in 'completions'.
    Then we bulk insert everything into your IPEDS-like tables:
      students, enrollments, course_enrollments, completions, courses.

    No nested functions reference 'nonlocal', so no scoping errors. All logic is inline.
    """

    random.seed(random_seed)

    # 1) Connect to DB & ensure foreign keys
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    # 2) Define the terms (Fall of each year)
    term_labels = []
    current_year = start_fall_year
    for _ in range(total_years):
        term_labels.append(f"Fall {current_year}")
        current_year += 1

    # 3) Insert a small set of courses if not present
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

    # Build a dict of {course_id: (code, name, ch)}
    course_dict = {}
    for i, (code, name, ch) in enumerate(possible_courses):
        cid = i + 1
        course_dict[cid] = (code, name, ch)

    # 4) Setup distributions
    letter_dist = [("A", 0.25), ("B", 0.35), ("C", 0.25), ("D", 0.1), ("F", 0.05)]
    letter_to_gpa = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
    race_categories = ["White","Black/African American","Hispanic/Latino","Asian","Two or More Races","Other/Unknown"]
    genders = ["Male","Female"]

    # 5) We'll maintain a list of all students in Python
    student_records = []
    next_student_id = 1

    # We'll store rows for these tables, then do bulk inserts at the end
    enrollment_rows = []
    course_enrollment_rows = []
    completion_rows = []

    # Keep counters for each table's PK
    enrollment_id_counter = 1
    course_enrollment_id_counter = 1
    completion_id_counter = 1

    # 6) Main loop over each Fall term
    for term_label in term_labels:
        # (A) Add new freshmen
        for _ in range(new_freshmen_each_fall):
            sid = next_student_id
            next_student_id += 1

            gender = random.choice(genders)
            fname = random.choice(["John","Mike","David","Chris","James","Mary","Linda","Jennifer","Susan","Elizabeth"])
            lname = random.choice(["Smith","Jones","Brown","Johnson","Miller","Davis","Garcia","Taylor","Wilson","Hernandez"])
            base_date = datetime.date(2025,1,7)
            age_days = random.randint(18*365,22*365)
            dob = base_date - datetime.timedelta(days=age_days)
            dob_str = dob.strftime("%Y-%m-%d")

            race = random.choice(race_categories)

            # Put them in class_year=1 (freshman), active
            student_rec = {
                "student_id": sid,
                "first_name": fname,
                "last_name": lname,
                "dob": dob_str,
                "gender": gender,
                "race_eth": race,
                "class_year": 1,
                "active": True
            }
            student_records.append(student_rec)

        # (B) For each active student, decide if they drop, remain, or graduate
        updated_students = []
        for s in student_records:
            if not s["active"]:
                updated_students.append(s)
                continue

            # base dropout
            dropout_chance = base_dropout_prob
            if s["race_eth"] == "Black/African American":
                dropout_chance += race_penalty_for_retention

            # random dropout?
            if random.random() < dropout_chance:
                s["active"] = False
                updated_students.append(s)
                continue

            # if senior, maybe graduate
            if s["class_year"] == 4:
                if random.random() < senior_grad_prob:
                    # graduate
                    s["active"] = False
                    completion_rows.append((
                        completion_id_counter,
                        s["student_id"],
                        random.choice(["Bachelor’s","Associate","Certificate <1 year"]),
                        random.choice(["11.0101","24.0101","52.0301","14.0901"]),
                        "2025-05-15"
                    ))
                    completion_id_counter += 1
                else:
                    # remain senior
                    pass
            else:
                # attempt class-year advancement
                cy = s["class_year"]
                if cy == 1 and random.random() < freshman_to_soph_prob:
                    s["class_year"] = 2
                elif cy == 2 and random.random() < soph_to_junior_prob:
                    s["class_year"] = 3
                elif cy == 3 and random.random() < junior_to_senior_prob:
                    s["class_year"] = 4

            updated_students.append(s)

        student_records = updated_students

        # (C) For each still-active student, create enrollment + courses
        for s in student_records:
            if not s["active"]:
                continue

            enrollment_id = enrollment_id_counter
            enrollment_id_counter += 1

            program = random.choice(["11.0101","24.0101","52.0301","14.0901"])
            status = "Active"

            enrollment_rows.append((
                enrollment_id,
                s["student_id"],
                term_label,
                program,
                status,
                0  # retained_next_term
            ))

            # pick 2..5 courses
            num_courses = random.randint(2,5)
            # convert dict_keys to list
            possible_course_ids = list(course_dict.keys())
            chosen_course_ids = random.sample(possible_course_ids, num_courses)

            for cid in chosen_course_ids:
                letter_chosen = "C"
                r = random.random()
                cum = 0.0
                for (lg, prob) in letter_dist:
                    cum += prob
                    if r <= cum:
                        letter_chosen = lg
                        break
                gp = letter_to_gpa[letter_chosen]

                course_enrollment_rows.append((
                    course_enrollment_id_counter,
                    enrollment_id,
                    cid,
                    letter_chosen,
                    gp
                ))
                course_enrollment_id_counter += 1

    # 7) Bulk Insert into DB
    # (A) students
    student_inserts = []
    for s in student_records:
        student_inserts.append((
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
    """, student_inserts)

    # (B) enrollments
    c.executemany("""
        INSERT INTO enrollments(enrollment_id, student_id, term, program, status, retained_next_term)
        VALUES (?, ?, ?, ?, ?, ?);
    """, enrollment_rows)

    # (C) course_enrollments
    c.executemany("""
        INSERT INTO course_enrollments(course_enrollment_id, enrollment_id, course_id, grade, grade_points)
        VALUES (?, ?, ?, ?, ?);
    """, course_enrollment_rows)

    # (D) completions
    c.executemany("""
        INSERT INTO completions(completion_id, student_id, award_type, cip_code, completion_date)
        VALUES (?, ?, ?, ?, ?);
    """, completion_rows)

    conn.commit()
    conn.close()

    print(f"Generated {len(student_records)} total unique students.")
    print(f"Enrollments inserted: {len(enrollment_rows)}.")
    print(f"Course enrollments inserted: {len(course_enrollment_rows)}.")
    print(f"Completions inserted: {len(completion_rows)}.")


if __name__ == "__main__":
    generate_stable_population_data()
