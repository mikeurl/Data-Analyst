"""
Student Data Anonymization Tool

This module anonymizes student-level data by replacing real student IDs with
randomized dummy IDs while maintaining a translation table for re-identification
if needed.

Use cases:
- Sharing data with external partners while protecting student privacy
- Creating demo datasets from real data
- Compliance with data privacy regulations

The tool generates:
1. Anonymized CSV with dummy student IDs
2. Translation table mapping dummy IDs to original IDs (keep secure!)

Security Note: The translation table allows re-identification. Store it securely
and separately from the anonymized data.
"""

import pandas as pd
import random
import argparse
import sys

def main(input_file, output_file, translation_file):
    # Load the CSV into a DataFrame
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Ensure the expected column exists
    if 'student_id' not in df.columns:
        print("Error: The input CSV must contain a 'student_id' column.")
        sys.exit(1)
    
    # Get the number of records
    n = len(df)
    if n == 0:
        print("Warning: The input CSV file is empty.")
        sys.exit(0)
    
    # Generate a list of unique dummy IDs.
    # Here we choose a range starting at 10,000,000 with a span large enough to accommodate all rows.
    try:
        dummy_ids = random.sample(range(10000000, 10000000 + n * 100), n)
    except ValueError as e:
        print(f"Error generating dummy IDs: {e}")
        sys.exit(1)
    
    # Create a translation DataFrame mapping dummy IDs to the original student IDs.
    translation_df = pd.DataFrame({
        'dummy_student_id': dummy_ids,
        'original_student_id': df['student_id']
    })
    
    # Replace the original student_id column with the dummy IDs in the main DataFrame.
    df['student_id'] = dummy_ids
    
    # Save the anonymized data and translation table to CSV files.
    try:
        df.to_csv(output_file, index=False)
        translation_df.to_csv(translation_file, index=False)
        print(f"Anonymized data written to: {output_file}")
        print(f"Translation table written to: {translation_file}")
    except Exception as e:
        print(f"Error writing output files: {e}")
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Anonymize a CSV file by randomizing 'student_id' and output a translation table."
    )
    parser.add_argument("input_file", help="Path to the input CSV file")
    parser.add_argument("output_file", help="Path to the output anonymized CSV file")
    parser.add_argument("translation_file", help="Path to the output translation table CSV file")
    
    args = parser.parse_args()
    main(args.input_file, args.output_file, args.translation_file)
