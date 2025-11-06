"""
Synthetic Student Completions Data Generator (CSV Format)

This module generates synthetic student-level completion data in CSV format,
separate from the SQLite database approach. This is useful for:
- Testing data validation scripts
- Creating sample datasets for reporting
- Demonstrating data anonymization workflows

The generated data includes:
- Student demographics (race/ethnicity, gender, age)
- Program information (CIP codes, award types)
- Delivery mode (online, hybrid, in-person)
- Institutional metadata

Note: This generates CSV data, not database records. For database population,
use SyntheticDataforSchema2.py instead.
"""

import pandas as pd
import numpy as np
import string
import random

def generate_synthetic_student_data(num_students=100, seed=42):
    """
    Generates a CSV-ready student completion dataset.

    Creates synthetic data for students who have completed programs, including
    demographic information, program details, and award types following IPEDS
    reporting standards.

    Args:
        num_students: Number of student records to generate (default: 100)
        seed: Random seed for reproducibility (default: 42)

    Returns:
        pandas.DataFrame: DataFrame with student completion records

    Output columns:
        - institution_name: Name of the institution
        - student_id: Unique student identifier (synthetic)
        - reporting_year: Academic year for reporting
        - cip_code: CIP (Classification of Instructional Programs) code
        - cip_program_name: Program name corresponding to CIP code
        - award_category: Certificate or Degree
        - award_subtype: Specific award level (Associate, Bachelor's, etc.)
        - program_delivery_mode: Fully online, Partly online, or Not online
        - race_ethnicity: Student race/ethnicity category
        - gender: Student gender
        - age: Student age at completion
        - unusual_notes: Any special circumstances or notes
    """
    np.random.seed(seed)
    
    # 1. Fixed institution + reporting year
    institution_name = "Example University"
    reporting_year = "2024-2025"
    
    # 2. CIP codes & corresponding example programs
    #    (feel free to modify these to your liking)
    cip_codes = {
        "52.0301": "Accounting",
        "14.0901": "Computer Engineering",
        "11.0101": "Computer Science",
        "24.0101": "Liberal Arts and Sciences",
        "26.0101": "Biology"
    }
    cip_code_list = list(cip_codes.keys())
    
    # 3. Award Categories & Subtypes
    award_categories = {
        "Certificate": [
            "Less than 1 year",
            "1-2 years"
        ],
        "Degree": [
            "Associate (2 years)",
            "Bachelor’s (4 years)",
            "Master’s (6+ years)",
            "Doctorate (highest level)"
        ]
    }
    
    # 4. Delivery Modes
    delivery_options = [
        "Fully online",
        "Partly online",
        "Not online"
    ]
    
    # 5. Race/Ethnicity Options
    #    Here each student is assigned exactly one category (simplified).
    race_ethnicity_options = [
        "Hispanic/Latino",
        "Asian",
        "Black/African American",
        "Native Hawaiian/Pacific Islander",
        "White",
        "Two or More Races",
        "American Indian/Alaska Native",
        "Race Unknown",
        "Non-US Resident"
    ]
    
    # 6. Gender Options
    gender_options = ["Male", "Female", "Other/Unknown"]
    
    # 7. Generate random "unusual" notes
    notes_options = [
        "No unusual circumstances.",
        "Program mostly online but requires on-campus lab sessions.",
        "Newly introduced Master’s track caused a spike in enrollments.",
        "Due to accreditation changes, some programs have been renamed.",
        "Recent hurricane disrupted campus, leading to delayed completions."
    ]
    
    # Container for rows
    rows = []
    
    for i in range(num_students):
        # Generate a unique-ish Student ID (not real PII, just a placeholder)
        # Example format: S + 7 random alphanumeric characters
        student_id = "S" + "".join(np.random.choice(list(string.digits + string.ascii_uppercase), 7))
        
        # Randomly pick CIP code & interpret the program name if you like
        cip_code = np.random.choice(cip_code_list)
        
        # Award category & subtype
        category = np.random.choice(list(award_categories.keys()))
        subtype = np.random.choice(award_categories[category])
        
        # Delivery mode
        delivery_mode = np.random.choice(delivery_options)
        
        # Race/Ethnicity, Gender
        race_eth = np.random.choice(race_ethnicity_options)
        gender = np.random.choice(gender_options)
        
        # Age (let's say from 17 to 60 for demonstration)
        age = np.random.randint(17, 61)
        
        # Notes
        unusual_note = np.random.choice(notes_options)
        
        row = {
            "institution_name": institution_name,
            "student_id": student_id,
            "reporting_year": reporting_year,
            "cip_code": cip_code,
            "cip_program_name": cip_codes[cip_code],  # e.g., "Accounting"
            "award_category": category,              # e.g. "Degree"
            "award_subtype": subtype,                # e.g. "Bachelor’s (4 years)"
            "program_delivery_mode": delivery_mode,   # e.g. "Fully online"
            "race_ethnicity": race_eth,              # e.g. "Black/African American"
            "gender": gender,                        # e.g. "Male"
            "age": age,
            "unusual_notes": unusual_note
        }
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    df = generate_synthetic_student_data(num_students=200, seed=42)
    df.to_csv("synthetic_student_level_data.csv", index=False)
    print("Student-level synthetic data generated in synthetic_student_level_data.csv.")

