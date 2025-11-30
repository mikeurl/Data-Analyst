"""
IPEDS Data Validation Script

This module provides validation functions for both:
1. CSV data files (legacy format for external data imports)
2. SQLite database integrity (for the application's database)

Validation checks include:
- Required column/table presence
- CIP code format validation
- Award type validation
- Gender field validation
- Data integrity checks
- Distribution analysis

Use this script before deploying or after data modifications.
"""

import pandas as pd
import sqlite3
import sys
import os
from typing import List, Optional, Tuple


def validate_csv_data(data_path: str) -> List[str]:
    """
    Validate CSV data file for IPEDS compliance.

    This validates external CSV files that might be imported.

    Args:
        data_path: Path to the CSV file to validate

    Returns:
        List of validation issues/warnings. Empty list if all checks pass.
    """
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        return [f"Error: File not found: {data_path}"]
    except Exception as e:
        return [f"Error: Could not read CSV file: {e}"]

    issues = []

    # 1. Check for empty file
    if df.empty:
        issues.append("Error: The file is empty. No data rows found.")
        return issues

    # 2. Check for common IPEDS columns
    # Support both old format (institution_name, etc.) and new format
    old_format_columns = [
        "institution_name", "student_id", "reporting_year", "cip_code",
        "award_category", "award_subtype", "program_delivery_mode",
        "race_ethnicity", "gender", "age"
    ]
    new_format_columns = [
        "student_id", "first_name", "last_name", "gender", "race_ethnicity"
    ]

    has_old_format = all(col in df.columns for col in old_format_columns)
    has_new_format = all(col in df.columns for col in new_format_columns)

    if not has_old_format and not has_new_format:
        missing_old = [c for c in old_format_columns if c not in df.columns]
        missing_new = [c for c in new_format_columns if c not in df.columns]
        issues.append(f"Error: Missing required columns. Missing from old format: {missing_old}")
        issues.append(f"       Missing from new format: {missing_new}")
        return issues

    # 3. Validate CIP codes if present
    if "cip_code" in df.columns:
        cip_code_pattern = r"^\d{2}\.\d{4}$"
        invalid_cip = df[~df["cip_code"].astype(str).str.match(cip_code_pattern)]
        if not invalid_cip.empty:
            issues.append(
                f"Warning: Found {len(invalid_cip)} invalid CIP code entries: "
                f"{invalid_cip['cip_code'].unique().tolist()[:5]}..."
            )

    # 4. Validate gender values
    if "gender" in df.columns:
        valid_genders = ["Male", "Female", "Other/Unknown"]
        invalid_gender_rows = df[~df["gender"].isin(valid_genders)]
        if not invalid_gender_rows.empty:
            issues.append(
                f"Warning: Found {len(invalid_gender_rows)} rows with invalid gender values"
            )

    # 5. Check for age range if present
    if "age" in df.columns:
        invalid_ages = df[(df["age"] < 0) | (df["age"] > 100)]
        if not invalid_ages.empty:
            issues.append(
                f"Warning: Found {len(invalid_ages)} age values outside expected range (0-100)"
            )

    # 6. Summary statistics
    issues.append(f"Info: Total rows: {len(df)}")
    if "cip_code" in df.columns:
        cip_counts = df["cip_code"].value_counts().head(5).to_dict()
        issues.append(f"Info: Top CIP codes: {cip_counts}")

    return issues


def validate_database(db_path: str = "ipeds_data.db") -> List[str]:
    """
    Validate the SQLite database integrity and data quality.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        List of validation issues/warnings. Empty list if all checks pass.
    """
    issues = []

    if not os.path.exists(db_path):
        return [f"Error: Database file not found: {db_path}"]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Check required tables exist
        required_tables = ["students", "enrollments", "courses", "course_enrollments", "completions"]
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]

        for table in required_tables:
            if table not in existing_tables:
                issues.append(f"Error: Missing required table: {table}")

        if issues:
            conn.close()
            return issues

        # 2. Check students table
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        issues.append(f"Info: Total students: {student_count}")

        if student_count == 0:
            issues.append("Warning: Students table is empty")
        else:
            # Check gender values
            cursor.execute("""
                SELECT gender, COUNT(*) as cnt
                FROM students
                GROUP BY gender
            """)
            gender_dist = cursor.fetchall()
            valid_genders = ["Male", "Female", "Other/Unknown"]
            for gender, count in gender_dist:
                if gender not in valid_genders:
                    issues.append(f"Warning: Invalid gender value found: '{gender}' ({count} records)")

            # Check race_ethnicity values
            cursor.execute("""
                SELECT race_ethnicity, COUNT(*) as cnt
                FROM students
                GROUP BY race_ethnicity
            """)
            race_dist = dict(cursor.fetchall())
            issues.append(f"Info: Race/ethnicity distribution: {race_dist}")

        # 3. Check enrollments table
        cursor.execute("SELECT COUNT(*) FROM enrollments")
        enrollment_count = cursor.fetchone()[0]
        issues.append(f"Info: Total enrollments: {enrollment_count}")

        if enrollment_count > 0:
            # Check for orphaned enrollments
            cursor.execute("""
                SELECT COUNT(*) FROM enrollments e
                WHERE NOT EXISTS (SELECT 1 FROM students s WHERE s.student_id = e.student_id)
            """)
            orphaned = cursor.fetchone()[0]
            if orphaned > 0:
                issues.append(f"Error: Found {orphaned} enrollments with invalid student_id")

            # Check GPA range
            cursor.execute("SELECT MIN(avg_gpa), MAX(avg_gpa) FROM enrollments WHERE avg_gpa IS NOT NULL")
            min_gpa, max_gpa = cursor.fetchone()
            if min_gpa is not None and max_gpa is not None:
                if min_gpa < 0 or max_gpa > 4.0:
                    issues.append(f"Warning: GPA values outside expected range [0, 4.0]: min={min_gpa}, max={max_gpa}")

            # Check CIP codes (program field)
            cursor.execute("SELECT DISTINCT program FROM enrollments")
            programs = [row[0] for row in cursor.fetchall()]
            cip_pattern = r"^\d{2}\.\d{4}$"
            import re
            for prog in programs:
                if prog and not re.match(cip_pattern, str(prog)):
                    issues.append(f"Warning: Invalid CIP code format: '{prog}'")

        # 4. Check completions table
        cursor.execute("SELECT COUNT(*) FROM completions")
        completion_count = cursor.fetchone()[0]
        issues.append(f"Info: Total completions: {completion_count}")

        if completion_count > 0:
            cursor.execute("SELECT award_type, COUNT(*) FROM completions GROUP BY award_type")
            award_dist = dict(cursor.fetchall())
            issues.append(f"Info: Award type distribution: {award_dist}")

        # 5. Check course_enrollments
        cursor.execute("SELECT COUNT(*) FROM course_enrollments")
        ce_count = cursor.fetchone()[0]
        issues.append(f"Info: Total course enrollments: {ce_count}")

        conn.close()

    except sqlite3.Error as e:
        issues.append(f"Error: Database error: {e}")

    return issues


def validate_student_data(data_path: str) -> List[str]:
    """
    Legacy function - validates CSV data.

    Maintained for backward compatibility.

    Args:
        data_path: Path to the CSV file to validate

    Returns:
        List of validation issues/warnings.
    """
    return validate_csv_data(data_path)


if __name__ == "__main__":
    print("=" * 70)
    print("IPEDS Data Validation Tool")
    print("=" * 70)

    # Check for command line argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if file_path.endswith('.db') or file_path.endswith('.sqlite'):
            print(f"\nValidating database: {file_path}")
            issues = validate_database(file_path)
        else:
            print(f"\nValidating CSV file: {file_path}")
            issues = validate_csv_data(file_path)
    else:
        # Default: validate the database if it exists, else look for CSV
        if os.path.exists("ipeds_data.db"):
            print("\nValidating database: ipeds_data.db")
            issues = validate_database("ipeds_data.db")
        elif os.path.exists("synthetic_student_level_data.csv"):
            print("\nValidating CSV file: synthetic_student_level_data.csv")
            issues = validate_csv_data("synthetic_student_level_data.csv")
        else:
            print("\nNo data file found. Please specify a file path.")
            print("Usage: python validate_data.py [file_path]")
            print("       Supports .db, .sqlite, and .csv files")
            sys.exit(1)

    print()
    if not issues:
        print("✓ All checks passed. No issues found.")
    else:
        for item in issues:
            if item.startswith("Error"):
                print(f"✗ {item}")
            elif item.startswith("Warning"):
                print(f"⚠ {item}")
            else:
                print(f"  {item}")

    # Exit with error code if there are errors
    has_errors = any(item.startswith("Error") for item in issues)
    sys.exit(1 if has_errors else 0)


