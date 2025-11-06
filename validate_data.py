import pandas as pd

def validate_student_data(data_path):
    """
    Loads the student-level data from CSV and performs basic validation checks.
    Returns a list of validation issues (empty if all checks pass).
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


