"""
IPEDS Fall Enrollment Query Engine

This module provides SQL queries and data aggregation for IPEDS Fall Enrollment
reporting. It generates data formatted for Parts A, B, C, E, and F.

Part A: Enrollment by race/ethnicity, gender, and attendance status
Part B: Enrollment by age
Part C: Residence of first-time students
Part E: Retention rates
Part F: Student-to-faculty ratio
"""

import sqlite3
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import os

DB_PATH = os.getenv("IPEDS_DB_PATH", "ipeds_data.db")

# IPEDS race/ethnicity categories in reporting order
IPEDS_RACE_ORDER = [
    "Nonresident Alien",
    "Hispanic/Latino",
    "American Indian/Alaska Native",
    "Asian",
    "Black/African American",
    "Native Hawaiian/Pacific Islander",
    "White",
    "Two or More Races",
    "Race/Ethnicity Unknown"
]

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


class IPEDSQueryEngine:
    """
    Query engine for generating IPEDS Fall Enrollment reports.

    Provides methods to generate data for each IPEDS Fall Enrollment part:
    - Part A: Race/Ethnicity/Gender enrollment
    - Part B: Age distribution
    - Part C: First-time student residence
    - Part E: Retention rates
    - Part F: Student-to-faculty ratio
    """

    def __init__(self, db_path: str = DB_PATH):
        """Initialize the query engine with database path."""
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path)

    def get_available_terms(self) -> list:
        """Get list of available Fall terms in the database."""
        conn = self._get_connection()
        query = """
            SELECT DISTINCT term
            FROM enrollments
            WHERE term LIKE 'Fall%'
            ORDER BY term DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df['term'].tolist()

    def generate_part_a(self, term: str) -> Dict[str, pd.DataFrame]:
        """
        Generate Part A: Enrollment by race/ethnicity, gender, and attendance status.

        Returns separate DataFrames for:
        - Full-time undergraduate enrollment
        - Part-time undergraduate enrollment

        Args:
            term: The term to report (e.g., "Fall 2024")

        Returns:
            Dictionary with 'full_time' and 'part_time' DataFrames
        """
        conn = self._get_connection()

        # Query for enrollment counts by race, gender, and attendance status
        query = """
            SELECT
                s.race_ethnicity,
                s.gender,
                e.attendance_status,
                e.enrollment_type,
                e.distance_education_status,
                COUNT(*) as count
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            WHERE e.term = ?
                AND e.level = 'Undergraduate'
            GROUP BY s.race_ethnicity, s.gender, e.attendance_status,
                     e.enrollment_type, e.distance_education_status
        """
        df = pd.read_sql_query(query, conn, params=(term,))
        conn.close()

        # Create pivot tables for full-time and part-time
        result = {}

        for attendance in ['Full-time', 'Part-time']:
            filtered = df[df['attendance_status'] == attendance]

            if filtered.empty:
                # Create empty DataFrame with proper structure
                pivot = pd.DataFrame(index=IPEDS_RACE_ORDER, columns=['Men', 'Women', 'Total'])
                pivot = pivot.fillna(0)
            else:
                pivot = filtered.pivot_table(
                    index='race_ethnicity',
                    columns='gender',
                    values='count',
                    aggfunc='sum',
                    fill_value=0
                )
                # Ensure proper column order
                for col in ['Men', 'Women']:
                    if col not in pivot.columns:
                        pivot[col] = 0
                pivot = pivot[['Men', 'Women']]
                pivot['Total'] = pivot['Men'] + pivot['Women']

                # Reindex to IPEDS order
                pivot = pivot.reindex(IPEDS_RACE_ORDER, fill_value=0)

            # Add grand total row
            pivot.loc['Grand Total'] = pivot.sum()

            result[attendance.lower().replace('-', '_')] = pivot

        return result

    def generate_part_b(self, term: str) -> pd.DataFrame:
        """
        Generate Part B: Enrollment by age.

        Returns enrollment counts by age category and gender.

        Args:
            term: The term to report (e.g., "Fall 2024")

        Returns:
            DataFrame with age categories as rows, gender as columns
        """
        conn = self._get_connection()

        # Calculate age at time of term and categorize
        query = """
            SELECT
                s.gender,
                CASE
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 18 THEN 'Under 18'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 20 THEN '18-19'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 22 THEN '20-21'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 25 THEN '22-24'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 30 THEN '25-29'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 35 THEN '30-34'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 40 THEN '35-39'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 50 THEN '40-49'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 < 65 THEN '50-64'
                    WHEN (julianday(e.term_start_date) - julianday(s.dob)) / 365.25 >= 65 THEN '65 and over'
                    ELSE 'Age unknown'
                END as age_category,
                COUNT(*) as count
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            WHERE e.term = ?
                AND e.level = 'Undergraduate'
            GROUP BY s.gender, age_category
        """
        df = pd.read_sql_query(query, conn, params=(term,))
        conn.close()

        if df.empty:
            pivot = pd.DataFrame(index=AGE_CATEGORIES, columns=['Men', 'Women', 'Total'])
            pivot = pivot.fillna(0)
        else:
            pivot = df.pivot_table(
                index='age_category',
                columns='gender',
                values='count',
                aggfunc='sum',
                fill_value=0
            )
            for col in ['Men', 'Women']:
                if col not in pivot.columns:
                    pivot[col] = 0
            pivot = pivot[['Men', 'Women']]
            pivot['Total'] = pivot['Men'] + pivot['Women']
            pivot = pivot.reindex(AGE_CATEGORIES, fill_value=0)

        pivot.loc['Grand Total'] = pivot.sum()
        return pivot

    def generate_part_c(self, term: str) -> pd.DataFrame:
        """
        Generate Part C: Residence of first-time students.

        Returns first-time student counts by state of residence.

        Args:
            term: The term to report (e.g., "Fall 2024")

        Returns:
            DataFrame with state residence data
        """
        conn = self._get_connection()

        query = """
            SELECT
                COALESCE(s.state_of_residence, 'Foreign Countries') as state,
                COALESCE(s.state_fips_code, '90') as fips_code,
                COUNT(*) as count
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            WHERE e.term = ?
                AND e.enrollment_type = 'First-time'
                AND e.level = 'Undergraduate'
            GROUP BY s.state_of_residence, s.state_fips_code
            ORDER BY count DESC
        """
        df = pd.read_sql_query(query, conn, params=(term,))
        conn.close()

        if df.empty:
            return pd.DataFrame(columns=['State', 'FIPS Code', 'First-time Students'])

        df.columns = ['State', 'FIPS Code', 'First-time Students']

        # Add total row
        total = pd.DataFrame({
            'State': ['Total First-time Students'],
            'FIPS Code': [''],
            'First-time Students': [df['First-time Students'].sum()]
        })
        df = pd.concat([df, total], ignore_index=True)

        return df

    def generate_part_e(self, cohort_year: int) -> Dict[str, Any]:
        """
        Generate Part E: Retention rates.

        Calculates retention rates for the specified cohort year.

        Args:
            cohort_year: The year the cohort entered (e.g., 2023)

        Returns:
            Dictionary containing retention rate data for full-time and part-time
        """
        conn = self._get_connection()

        query = """
            SELECT
                attendance_status,
                COUNT(*) as cohort_count,
                SUM(is_excluded) as exclusions,
                SUM(CASE WHEN is_excluded = 0 THEN 1 ELSE 0 END) as adjusted_cohort,
                SUM(CASE WHEN is_excluded = 0 AND (retained_fall = 1 OR completed_by_fall = 1) THEN 1 ELSE 0 END) as retained_or_completed
            FROM cohorts
            WHERE cohort_year = ?
                AND enrollment_type = 'First-time'
            GROUP BY attendance_status
        """
        df = pd.read_sql_query(query, conn, params=(cohort_year,))
        conn.close()

        result = {
            'cohort_year': cohort_year,
            'full_time': {
                'cohort': 0,
                'exclusions': 0,
                'adjusted_cohort': 0,
                'retained_or_completed': 0,
                'retention_rate': 0.0
            },
            'part_time': {
                'cohort': 0,
                'exclusions': 0,
                'adjusted_cohort': 0,
                'retained_or_completed': 0,
                'retention_rate': 0.0
            }
        }

        for _, row in df.iterrows():
            key = 'full_time' if row['attendance_status'] == 'Full-time' else 'part_time'
            result[key]['cohort'] = int(row['cohort_count'])
            result[key]['exclusions'] = int(row['exclusions'])
            result[key]['adjusted_cohort'] = int(row['adjusted_cohort'])
            result[key]['retained_or_completed'] = int(row['retained_or_completed'])

            if result[key]['adjusted_cohort'] > 0:
                result[key]['retention_rate'] = round(
                    result[key]['retained_or_completed'] / result[key]['adjusted_cohort'] * 100, 1
                )

        return result

    def generate_part_f(self, term: str) -> Dict[str, Any]:
        """
        Generate Part F: Student-to-faculty ratio.

        Calculates the student-to-faculty ratio for the specified term.

        Args:
            term: The term to report (e.g., "Fall 2024")

        Returns:
            Dictionary containing ratio calculation details
        """
        conn = self._get_connection()

        # Get student FTE (full-time + 1/3 part-time)
        student_query = """
            SELECT
                SUM(CASE WHEN attendance_status = 'Full-time' THEN 1 ELSE 0 END) as full_time_students,
                SUM(CASE WHEN attendance_status = 'Part-time' THEN 1 ELSE 0 END) as part_time_students
            FROM enrollments
            WHERE term = ?
                AND level = 'Undergraduate'
        """
        student_df = pd.read_sql_query(student_query, conn, params=(term,))

        # Get faculty FTE
        faculty_query = """
            SELECT
                SUM(fte_value) as total_fte
            FROM instructional_staff
            WHERE term = ?
                AND primary_function = 'Instruction'
        """
        faculty_df = pd.read_sql_query(faculty_query, conn, params=(term,))
        conn.close()

        ft_students = int(student_df['full_time_students'].iloc[0] or 0)
        pt_students = int(student_df['part_time_students'].iloc[0] or 0)
        student_fte = ft_students + (pt_students / 3)

        faculty_fte = float(faculty_df['total_fte'].iloc[0] or 0)

        ratio = round(student_fte / faculty_fte, 1) if faculty_fte > 0 else 0

        return {
            'term': term,
            'full_time_students': ft_students,
            'part_time_students': pt_students,
            'student_fte': round(student_fte, 1),
            'faculty_fte': round(faculty_fte, 1),
            'ratio': ratio,
            'ratio_display': f"{ratio}:1"
        }

    def generate_full_report(self, term: str) -> Dict[str, Any]:
        """
        Generate complete IPEDS Fall Enrollment report for a term.

        Args:
            term: The term to report (e.g., "Fall 2024")

        Returns:
            Dictionary containing all parts of the report
        """
        # Extract year from term for cohort calculation
        year = int(term.split()[-1])
        cohort_year = year - 1  # Previous year's cohort for retention

        return {
            'term': term,
            'generated_at': datetime.now().isoformat(),
            'part_a': self.generate_part_a(term),
            'part_b': self.generate_part_b(term),
            'part_c': self.generate_part_c(term),
            'part_e': self.generate_part_e(cohort_year),
            'part_f': self.generate_part_f(term)
        }

    def format_part_a_html(self, part_a_data: Dict[str, pd.DataFrame]) -> str:
        """Format Part A data as HTML table."""
        html = "<h3>Part A: Enrollment by Race/Ethnicity and Gender</h3>"

        for status, label in [('full_time', 'Full-time'), ('part_time', 'Part-time')]:
            df = part_a_data[status]
            html += f"<h4>{label} Undergraduate Students</h4>"
            html += df.to_html(classes='ipeds-table')

        return html

    def format_part_b_html(self, part_b_data: pd.DataFrame) -> str:
        """Format Part B data as HTML table."""
        html = "<h3>Part B: Enrollment by Age</h3>"
        html += part_b_data.to_html(classes='ipeds-table')
        return html

    def format_part_c_html(self, part_c_data: pd.DataFrame) -> str:
        """Format Part C data as HTML table."""
        html = "<h3>Part C: Residence of First-time Students</h3>"
        html += part_c_data.to_html(classes='ipeds-table', index=False)
        return html

    def format_part_e_html(self, part_e_data: Dict[str, Any]) -> str:
        """Format Part E data as HTML table."""
        html = f"<h3>Part E: Retention Rates (Cohort Year: {part_e_data['cohort_year']})</h3>"

        html += "<table class='ipeds-table'>"
        html += "<tr><th></th><th>Full-time</th><th>Part-time</th></tr>"
        html += f"<tr><td>Initial Cohort</td><td>{part_e_data['full_time']['cohort']}</td><td>{part_e_data['part_time']['cohort']}</td></tr>"
        html += f"<tr><td>Exclusions</td><td>{part_e_data['full_time']['exclusions']}</td><td>{part_e_data['part_time']['exclusions']}</td></tr>"
        html += f"<tr><td>Adjusted Cohort</td><td>{part_e_data['full_time']['adjusted_cohort']}</td><td>{part_e_data['part_time']['adjusted_cohort']}</td></tr>"
        html += f"<tr><td>Retained/Completed</td><td>{part_e_data['full_time']['retained_or_completed']}</td><td>{part_e_data['part_time']['retained_or_completed']}</td></tr>"
        html += f"<tr><td><strong>Retention Rate</strong></td><td><strong>{part_e_data['full_time']['retention_rate']}%</strong></td><td><strong>{part_e_data['part_time']['retention_rate']}%</strong></td></tr>"
        html += "</table>"

        return html

    def format_part_f_html(self, part_f_data: Dict[str, Any]) -> str:
        """Format Part F data as HTML table."""
        html = f"<h3>Part F: Student-to-Faculty Ratio ({part_f_data['term']})</h3>"

        html += "<table class='ipeds-table'>"
        html += f"<tr><td>Full-time Students</td><td>{part_f_data['full_time_students']}</td></tr>"
        html += f"<tr><td>Part-time Students</td><td>{part_f_data['part_time_students']}</td></tr>"
        html += f"<tr><td>Student FTE</td><td>{part_f_data['student_fte']}</td></tr>"
        html += f"<tr><td>Faculty FTE</td><td>{part_f_data['faculty_fte']}</td></tr>"
        html += f"<tr><td><strong>Student-to-Faculty Ratio</strong></td><td><strong>{part_f_data['ratio_display']}</strong></td></tr>"
        html += "</table>"

        return html


def get_ipeds_engine(db_path: str = DB_PATH) -> IPEDSQueryEngine:
    """Factory function to create an IPEDSQueryEngine instance."""
    return IPEDSQueryEngine(db_path)


if __name__ == "__main__":
    # Demo usage
    engine = get_ipeds_engine()
    terms = engine.get_available_terms()

    if terms:
        print(f"Available terms: {terms}")
        term = terms[0]
        print(f"\nGenerating report for {term}...")

        report = engine.generate_full_report(term)

        print("\n=== Part A: Full-time Enrollment ===")
        print(report['part_a']['full_time'])

        print("\n=== Part B: Age Distribution ===")
        print(report['part_b'])

        print("\n=== Part C: Residence ===")
        print(report['part_c'])

        print("\n=== Part E: Retention Rates ===")
        print(report['part_e'])

        print("\n=== Part F: Student-to-Faculty Ratio ===")
        print(report['part_f'])
    else:
        print("No terms found in database. Run the synthetic data generator first.")
