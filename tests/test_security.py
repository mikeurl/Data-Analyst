"""
Unit tests for security-critical functions in the IPEDS Data Analysis Toolkit.

These tests verify that SQL injection prevention, input validation,
and other security measures are working correctly.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_sql_python_assistant import (
    validate_sql_safety,
    check_user_intent,
    remove_sql_fences,
    remove_python_fences,
)


class TestSQLSafetyValidation:
    """Tests for validate_sql_safety function."""

    def test_valid_select(self):
        """Simple SELECT should pass validation."""
        sql = "SELECT * FROM students WHERE student_id = 1;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is True
        assert error is None

    def test_valid_select_with_join(self):
        """SELECT with JOIN should pass validation."""
        sql = """
        SELECT s.first_name, e.term, e.avg_gpa
        FROM students s
        JOIN enrollments e ON s.student_id = e.student_id
        WHERE e.avg_gpa > 3.0;
        """
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is True
        assert error is None

    def test_valid_temp_table(self):
        """CREATE TEMPORARY TABLE should pass validation."""
        sql = """
        CREATE TEMPORARY TABLE temp_analysis AS
        SELECT student_id, AVG(avg_gpa) as mean_gpa
        FROM enrollments GROUP BY student_id;
        """
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is True
        assert error is None

    def test_block_drop_table(self):
        """DROP TABLE should be blocked."""
        sql = "DROP TABLE students;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "DROP" in error

    def test_block_delete(self):
        """DELETE should be blocked."""
        sql = "DELETE FROM students WHERE student_id = 1;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "DELETE" in error

    def test_block_update(self):
        """UPDATE should be blocked."""
        sql = "UPDATE students SET first_name = 'Hacked' WHERE student_id = 1;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "UPDATE" in error

    def test_block_insert_permanent(self):
        """INSERT into permanent tables should be blocked."""
        sql = "INSERT INTO students (first_name) VALUES ('Hacked');"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "INSERT" in error

    def test_block_truncate(self):
        """TRUNCATE should be blocked."""
        sql = "TRUNCATE TABLE students;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "TRUNCATE" in error

    def test_block_alter(self):
        """ALTER should be blocked."""
        sql = "ALTER TABLE students ADD COLUMN hacked TEXT;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "ALTER" in error

    def test_block_pragma(self):
        """PRAGMA should be blocked."""
        sql = "PRAGMA table_info(students);"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "PRAGMA" in error

    def test_block_attach(self):
        """ATTACH should be blocked."""
        sql = "ATTACH DATABASE '/tmp/malicious.db' AS malicious;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "ATTACH" in error

    def test_block_create_permanent_table(self):
        """CREATE TABLE (without TEMP) should be blocked."""
        sql = "CREATE TABLE hacked (id INTEGER);"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "CREATE" in error.lower() or "TEMPORARY" in error

    def test_comment_bypass_single_line(self):
        """Comments should not allow bypassing security."""
        sql = "SELECT * FROM students; -- DROP TABLE students;"
        is_safe, error = validate_sql_safety(sql)
        # Should pass because DROP is in a comment
        assert is_safe is True

    def test_comment_bypass_multi_line(self):
        """Multi-line comments should not allow bypassing security."""
        sql = "SELECT * FROM students /* DROP TABLE students */;"
        is_safe, error = validate_sql_safety(sql)
        # Should pass because DROP is in a comment
        assert is_safe is True

    def test_actual_drop_not_in_comment(self):
        """Actual DROP statements (not in comments) should be blocked."""
        sql = """
        SELECT * FROM students;
        DROP TABLE students;
        """
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False
        assert "DROP" in error

    def test_case_insensitive_blocking(self):
        """SQL keywords should be blocked regardless of case."""
        sql = "drop TABLE students;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False

        sql = "DrOp TaBlE students;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False

    def test_no_select_no_temp_rejected(self):
        """SQL without SELECT or CREATE TEMP should be rejected."""
        sql = "SHOW TABLES;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False


class TestUserIntentCheck:
    """Tests for check_user_intent function."""

    def test_safe_question(self):
        """Normal data questions should pass."""
        is_safe, warning = check_user_intent("How many students are enrolled?")
        assert is_safe is True
        assert warning is None

    def test_safe_analysis_request(self):
        """Analysis requests should pass."""
        is_safe, warning = check_user_intent("What are the retention rates by gender?")
        assert is_safe is True
        assert warning is None

    def test_block_drop_request(self):
        """Requests to drop data should be blocked."""
        is_safe, warning = check_user_intent("Drop the students table")
        assert is_safe is False
        assert warning is not None
        assert "DROP" in warning.upper() or "Destructive" in warning

    def test_block_delete_request(self):
        """Requests to delete data should be blocked."""
        is_safe, warning = check_user_intent("Delete all records from enrollments")
        assert is_safe is False

    def test_block_update_request(self):
        """Requests to update data should be blocked."""
        is_safe, warning = check_user_intent("Update the GPA to 4.0 where student_id = 1")
        assert is_safe is False


class TestCodeFenceRemoval:
    """Tests for code fence removal functions."""

    def test_remove_sql_fences(self):
        """SQL code fences should be removed."""
        sql_with_fences = "```sql\nSELECT * FROM students;\n```"
        result = remove_sql_fences(sql_with_fences)
        assert result == "SELECT * FROM students;"
        assert "```" not in result

    def test_remove_sql_fences_no_language(self):
        """Generic code fences should also be removed."""
        sql_with_fences = "```\nSELECT * FROM students;\n```"
        result = remove_sql_fences(sql_with_fences)
        assert result == "SELECT * FROM students;"

    def test_remove_sql_fences_clean_input(self):
        """Already clean input should remain unchanged."""
        clean_sql = "SELECT * FROM students;"
        result = remove_sql_fences(clean_sql)
        assert result == "SELECT * FROM students;"

    def test_remove_python_fences(self):
        """Python code fences should be removed."""
        py_with_fences = "```python\nprint('hello')\n```"
        result = remove_python_fences(py_with_fences)
        assert result == "print('hello')"
        assert "```" not in result

    def test_remove_python_fences_clean_input(self):
        """Already clean Python should remain unchanged."""
        clean_py = "print('hello')"
        result = remove_python_fences(clean_py)
        assert result == "print('hello')"


class TestSQLInjectionPrevention:
    """Tests for SQL injection attack prevention."""

    def test_union_injection(self):
        """UNION-based injection attempts should be safe (read-only)."""
        # UNION is actually allowed since it's read-only
        sql = "SELECT * FROM students UNION SELECT * FROM enrollments;"
        is_safe, error = validate_sql_safety(sql)
        # UNION is allowed for SELECT queries
        assert is_safe is True

    def test_stacked_queries_injection(self):
        """Stacked queries with dangerous commands should be blocked."""
        sql = "SELECT * FROM students; DROP TABLE students;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is False

    def test_blind_injection_safe(self):
        """Boolean-based blind injection is safe (read-only)."""
        sql = "SELECT * FROM students WHERE student_id = 1 AND 1=1;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is True

    def test_time_based_injection_safe(self):
        """Time-based injection attempts are limited to read-only."""
        # CASE statements are fine in SELECT
        sql = "SELECT * FROM students WHERE student_id = CASE WHEN 1=1 THEN 1 ELSE 2 END;"
        is_safe, error = validate_sql_safety(sql)
        assert is_safe is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
