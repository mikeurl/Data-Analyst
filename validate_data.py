"""
IPEDS Student Data Validation Script

This module validates student completion data CSV files to ensure data quality
and compliance with IPEDS reporting standards.

Validation checks include:
- Required column presence
- CIP code format validation
- Award category/subtype consistency
- Age range validation
- Gender field validation
- Distribution analysis

Use this script before submitting data or loading into analysis tools.
"""

import pandas as pd
import sys

def validate_student_data(data_path):
    """
    Performs comprehensive validation on student completion CSV data.

    Checks include:
    1. File not empty
    2. Required columns present
    3. CIP codes match expected format (XX.XXXX)
    4. Award categories and subtypes are valid combinations
    5. Age values are within reasonable range (0-100)
    6. Gender values are from expected set
    7. CIP code distribution summary

    Args:
        data_path: Path to the CSV file to validate

    Returns:
        list: List of validation issues/warnings. Empty list if all checks pass.
              Last item is always an info message with CIP code distribution.

    Example:
        issues = validate_student_data("synthetic_student_level_data.csv")
        if any("Error" in issue for issue in issues):
            print("Validation failed!")
        else:
            print("Validation passed!")
    """
    df = pd.read_csv(data_path)
    
    issues = []

    # 1. Check for empty file
    if df.empty:
        issues.append("Error: The file is empty. No data rows found.")
        return issues  # stop here if there's no data

    # 2. Required columns exist
    required_columns = [
        "institution_name",
        "student_id",
        "reporting_year",
        "cip_code",
        "award_category",
        "award_subtype",
        "program_delivery_mode",
        "race_ethnicity",
        "gender",
        "age"
    ]
    for col in required_columns:
        if col not in df.columns:
            issues.append(f"Error: Missing required column: {col}")

    # If required columns are missing, no need to keep checking
    if issues:
        return issues

    # 3. Check CIP codes for known patterns or your own CIP code list
    #    For demonstration, let's ensure they match a typical "xx.xxxx" format
    #    Or you might load a real CIP code list from IPEDS references
    cip_code_pattern = r"^\d{2}\.\d{4}$"
    invalid_cip = df[~df["cip_code"].astype(str).str.match(cip_code_pattern)]
    if not invalid_cip.empty:
        issues.append(
            f"Warning: Found {len(invalid_cip)} invalid CIP code entries:\n{invalid_cip['cip_code'].unique()}"
        )

    # 4. Check for valid award_category & award_subtype combos
    valid_award_combos = {
        "Certificate": ["Less than 1 year", "1-2 years"],
        "Degree": [
            "Associate (2 years)",
            "Bachelor’s (4 years)",
            "Master’s (6+ years)",
            "Doctorate (highest level)"
        ]
    }
    for idx, row in df.iterrows():
        cat = row["award_category"]
        sub = row["award_subtype"]
        if cat not in valid_award_combos:
            issues.append(f"Warning (row {idx}): Unknown award_category '{cat}'.")
        else:
            if sub not in valid_award_combos[cat]:
                issues.append(
                    f"Warning (row {idx}): award_subtype '{sub}' not valid for category '{cat}'."
                )

    # 5. Check ages (example: no negative, no extremely high ages, etc.)
    invalid_ages = df[(df["age"] < 0) | (df["age"] > 100)]
    if not invalid_ages.empty:
        issues.append(
            f"Warning: Found age values outside expected range (0-100):\n{invalid_ages[['student_id','age']]}"
        )

    # 6. Check gender field for unexpected entries
    valid_genders = ["Male", "Female", "Other/Unknown"]
    invalid_gender_rows = df[~df["gender"].isin(valid_genders)]
    if not invalid_gender_rows.empty:
        issues.append(
            f"Warning: Found invalid gender values:\n{invalid_gender_rows[['student_id','gender']]}"
        )

    # 7. Print a quick summary of how many rows we have for each CIP code
    #    (not exactly a validation, but a useful overview)
    cip_counts = df["cip_code"].value_counts().to_dict()
    issues.append(f"Info: CIP code distribution:\n{cip_counts}")

    return issues


if __name__ == "__main__":
    data_file_path = "synthetic_student_level_data.csv"  # update if needed
    validation_issues = validate_student_data(data_file_path)

    if not validation_issues:
        print("All checks passed. No issues found.")
    else:
        for item in validation_issues:
            print(item)


