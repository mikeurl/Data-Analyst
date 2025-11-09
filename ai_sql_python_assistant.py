"""
IPEDS Data AI Assistant - SQL & Python Query Interface

This module provides an AI-powered interface for querying IPEDS (Integrated
Postsecondary Education Data System) data using natural language. It uses
OpenAI's GPT models to convert user questions into SQL queries and Python
analysis code.

Features:
- Dynamic schema introspection from SQLite database
- Three-step workflow: SQL generation → Python analysis → Natural language explanation
- Automatic code fence removal from GPT responses
- Gradio web interface for easy interaction

Security Note: This script uses exec() for code execution. Use only with trusted
inputs and in controlled environments. Not recommended for production use without
additional security measures.
"""

import os
import re
import sqlite3
import sys

from openai import OpenAI
import gradio as gr
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt

# Import database setup functions for auto-initialization
from create_ipeds_db_schema import create_ipeds_db_schema
from SyntheticDataforSchema2 import generate_stable_population_data

###############################################################################
# 1. CONFIGURATION
###############################################################################

DB_PATH = "ipeds_data.db"  # Path to your SQLite DB file.

# Get OpenAI API key from environment variable - will create client when needed
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")
if not DEFAULT_API_KEY:
    print("\n" + "="*70)
    print("WARNING: OPENAI_API_KEY environment variable not set.")
    print("="*70)
    print("The web interface will start, but you won't be able to ask questions")
    print("until you set your API key.")
    print("\nTo set your API key:")
    print("  Windows: set OPENAI_API_KEY=your_key_here")
    print("  Mac/Linux: export OPENAI_API_KEY=your_key_here")
    print("\nOr add it to a .env file and load it with python-dotenv")
    print("="*70 + "\n")

###############################################################################
# 2. DYNAMIC SCHEMA FETCHING
###############################################################################

def get_live_schema_info(db_path=DB_PATH):
    """
    Connects to the SQLite database, enumerates all tables, columns, and FK relationships,
    and returns a textual summary that GPT can use to know the current schema.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all user tables (exclude internal sqlite_ tables)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]

    schema_text = ["CURRENT SQLITE SCHEMA:"]

    for table in tables:
        schema_text.append(f"\nTABLE: {table}")

        # Columns info
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()  # (cid, name, type, notnull, dflt_value, pk)
        schema_text.append("  COLUMNS:")
        for col in columns:
            cid, name, ctype, notnull, dflt, pk = col
            pk_flag = " (PK)" if pk else ""
            schema_text.append(f"    - {name} {ctype}{pk_flag}")

        # Foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        fkeys = cursor.fetchall()  # (id, seq, table, from_col, to_col, on_update, on_delete, match)
        if fkeys:
            schema_text.append("  FOREIGN KEYS:")
            for fk in fkeys:
                _, _, ref_table, from_col, to_col, *_ = fk
                schema_text.append(f"    - {from_col} -> {ref_table}.{to_col}")
        else:
            schema_text.append("  FOREIGN KEYS: None")

    conn.close()
    return "\n".join(schema_text)

###############################################################################
# 3. HELPER FUNCTIONS
###############################################################################

def remove_sql_fences(sql_text):
    """
    Removes triple-backtick fences or ```sql from GPT's SQL code.
    Example input:
      ```sql
      SELECT * FROM ...
      ```
    Returns clean SQL: SELECT * FROM ...
    """
    pattern = r"```(?:sql)?\n(.*?)\n```"
    match = re.search(pattern, sql_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        # Also remove any stray ``` if partial
        return sql_text.replace("```", "").strip()

def remove_python_fences(py_text):
    """
    Removes triple-backtick fences or ```python from GPT's Python code.
    Returns the cleaned Python code so exec() won't fail.
    """
    pattern = r"```(?:python)?\n(.*?)\n```"
    match = re.search(pattern, py_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return py_text.replace("```", "").strip()

def run_sql(sql_query):
    """
    Executes the given SQL query against DB_PATH and returns a pandas DataFrame.
    If there's an error, returns an error string instead.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df
    except Exception as e:
        return f"SQL Error: {str(e)}"

def run_python_code(py_code, df):
    """
    Executes the provided Python code snippet in a restricted local environment
    containing 'df' (the DataFrame from the SQL step), 'pd' (pandas), 'np' (numpy),
    'plt' (matplotlib.pyplot), 'tempfile', and 'os' for creating charts.
    Expects the code to store its final output in a variable named 'result'.
    Optionally, the code can store a chart file path in 'result_image'.
    Returns a tuple: (result_text, image_path or None)
    """
    import tempfile
    import os

    local_vars = {
        "df": df,
        "pd": pd,
        "np": np,
        "plt": plt,
        "tempfile": tempfile,
        "os": os
    }
    try:
        exec(py_code, {}, local_vars)
        output = local_vars.get("result", "No 'result' variable set.")
        image_path = local_vars.get("result_image", None)
        return str(output), image_path
    except Exception as e:
        return f"Python Error: {str(e)}", None

###############################################################################
# 4. GPT INTERACTION
###############################################################################

def check_question_relevance(user_input, client):
    """
    Checks if the user's question is actually about data that could be in the database.
    Rejects general knowledge questions, calculations, or off-topic queries.

    Returns: (is_relevant: bool, error_message: str or None)
    """
    schema_info = get_live_schema_info(DB_PATH)

    prompt = f"""
You are a gatekeeper for a higher education data analysis system.

DATABASE SCHEMA:
{schema_info}

USER'S QUESTION:
{user_input}

TASK: Determine if this question can be answered using the database.

ACCEPT questions about:
- Student data, enrollment, demographics, retention, graduation
- GPA, class year, programs, terms
- Statistics, trends, comparisons, correlations from the data
- Any analysis that requires querying the student database

REJECT questions about:
- General knowledge (capitals, definitions, history, etc.)
- Math problems or calculations not related to the data
- Questions about other topics/domains not in the database
- Requests for information that clearly isn't in a student database

Respond with ONLY:
YES - if the question is about data in the database
NO - if the question is off-topic or general knowledge

Then on a new line, briefly explain your reasoning (1 sentence).
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.0
    )

    decision_text = response.choices[0].message.content.strip()
    lines = decision_text.split('\n', 1)
    decision = lines[0].strip().upper()
    reason = lines[1].strip() if len(lines) > 1 else "No reason provided"

    is_relevant = decision.startswith('YES')

    if not is_relevant:
        error_message = f"""🤔 **Question Outside Database Scope**

Your question doesn't appear to be about the student data in this database.

**Reason:** {reason}

**This tool can answer questions like:**
- "How many students are enrolled?"
- "What are the retention rates by demographics?"
- "Show me GPA trends over time"
- "Which programs have the highest graduation rates?"

**This tool cannot answer:**
- General knowledge questions
- Math problems unrelated to the data
- Questions about topics outside higher education student data

Please ask a question about the student enrollment, demographics, academic performance, or related data in the database.
"""
        return False, error_message

    return True, None

def check_user_intent(user_input):
    """
    Checks if the user is asking for a destructive operation.
    This catches requests BEFORE SQL is generated, so we can warn users
    rather than silently converting their request to a SELECT.

    Returns: (is_safe: bool, warning_message: str or None)
    """
    # Normalize input
    user_normalized = user_input.lower()

    # Destructive intent keywords and phrases
    # Use .* to allow words between verb and object (e.g., "drop the students table")
    destructive_patterns = [
        (r'\b(drop|delete|remove|erase).*(table|database|column)',
         'DROP/DELETE operations'),
        (r'\b(delete|remove|erase).*(all|everything|rows?|records?|data|from)',
         'DELETE operations'),
        (r'\b(update|modify|change|edit|set).*(to|=|where)',
         'UPDATE operations'),
        (r'\b(truncate|clear|wipe).*(table|database|data)',
         'TRUNCATE operations'),
        (r'\b(alter|rename).*(table|column|database)',
         'ALTER operations'),
        (r'\b(insert|add).*(into|to)\s+(?!temp|temporary)',
         'INSERT operations into permanent tables'),
        (r'\bcreate\s+table\s+(?!temp|temporary)',
         'CREATE permanent table operations'),
    ]

    for pattern, operation_type in destructive_patterns:
        if re.search(pattern, user_normalized):
            return False, f"🛡️ **Destructive Operation Detected**\n\nYour request appears to ask for **{operation_type}**, which are not allowed in this read-only interface.\n\n**This interface is designed for data analysis only.**\n\nYou can:\n- ✅ Query data with SELECT statements\n- ✅ Analyze trends, statistics, and patterns\n- ✅ Create temporary tables for complex analysis\n\nYou cannot:\n- ❌ Modify, delete, or drop existing data\n- ❌ Create permanent tables or alter schema\n\nPlease rephrase your question to focus on analyzing or viewing data rather than modifying it."

    return True, None

def validate_sql_safety(sql_code):
    """
    Validates that SQL contains only safe, read-only operations.
    Allows: SELECT statements and CREATE TEMP/TEMPORARY TABLE
    Blocks: DROP, DELETE, UPDATE, INSERT (into permanent tables), ALTER, etc.

    Returns: (is_safe: bool, error_message: str or None)
    """
    # Normalize the SQL: uppercase, remove extra whitespace
    sql_normalized = ' '.join(sql_code.upper().split())

    # Remove comments to avoid bypasses like "-- DROP" in comments
    # Remove single-line comments (-- comment)
    sql_no_comments = '\n'.join([
        line.split('--')[0] for line in sql_code.split('\n')
    ])
    # Remove multi-line comments (/* comment */)
    sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_no_comments, flags=re.DOTALL)
    sql_normalized = ' '.join(sql_no_comments.upper().split())

    # Dangerous keywords that should never appear (even in temp table contexts)
    dangerous_keywords = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER',
        'GRANT', 'REVOKE', 'EXECUTE', 'EXEC',
        'ATTACH', 'DETACH', 'PRAGMA'
    ]

    for keyword in dangerous_keywords:
        # Use word boundaries to avoid false positives (e.g., "DROPPED" column name)
        if re.search(rf'\b{keyword}\b', sql_normalized):
            return False, f"Unsafe SQL operation detected: '{keyword}'. Only SELECT queries and temporary tables are allowed."

    # Check for UPDATE - must be very careful
    if re.search(r'\bUPDATE\b', sql_normalized):
        return False, "Unsafe SQL operation detected: 'UPDATE'. Only SELECT queries and temporary tables are allowed."

    # Check for INSERT - only allow into temp tables
    if re.search(r'\bINSERT\b', sql_normalized):
        # Check if it's inserting into a temp table
        # Pattern: INSERT INTO temp.tablename or INSERT INTO TEMP tablename
        if not re.search(r'\bINSERT\s+INTO\s+(TEMP\.|TEMPORARY\.|TEMP\s|TEMPORARY\s)', sql_normalized):
            return False, "Unsafe SQL operation detected: 'INSERT'. Only SELECT queries and temporary tables are allowed."

    # Must contain SELECT or CREATE TEMP/TEMPORARY TABLE
    has_select = re.search(r'\bSELECT\b', sql_normalized)
    has_temp_create = re.search(r'\bCREATE\s+(TEMP|TEMPORARY)\s+TABLE\b', sql_normalized)

    if not (has_select or has_temp_create):
        return False, "SQL must contain a SELECT statement or CREATE TEMPORARY TABLE."

    # Additional check: if it contains CREATE, ensure it's TEMP/TEMPORARY
    if re.search(r'\bCREATE\b', sql_normalized):
        if not re.search(r'\bCREATE\s+(TEMP|TEMPORARY)\s+TABLE\b', sql_normalized):
            return False, "Only CREATE TEMPORARY TABLE is allowed, not CREATE TABLE for permanent tables."

    return True, None

def ask_gpt_for_sql(user_question, client):
    """
    1) Fetch the live schema from the DB.
    2) Prompt GPT to write a SQL query (SQLite syntax) with no code fences.
    3) Return the raw GPT response (which may still have fences).
    """
    schema_info = get_live_schema_info(DB_PATH)

    prompt = f"""
You are an AI that writes SQL queries for a SQLite database.
Below is the current schema:

{schema_info}

The user wants the following:
{user_question}

CRITICAL SECURITY REQUIREMENTS:
- You MUST ONLY generate SELECT queries for reading data
- You MAY use CREATE TEMP TABLE or CREATE TEMPORARY TABLE if complex analysis requires it
- You MUST NEVER generate: DROP, DELETE, UPDATE, INSERT (into permanent tables), ALTER, TRUNCATE, or any other data modification statements
- This is a READ-ONLY interface for data analysis

Please provide ONLY the SQL code, no triple backticks. End with a semicolon.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content

def should_run_python_analysis(user_question, sql_code, df_preview, client):
    """
    Asks GPT whether Python analysis would add value beyond the SQL results.

    Simple queries (counts, lists, basic filters) often don't need Python.
    Complex queries (predictions, correlations, trends, statistical analysis) do.

    Returns: (should_run: bool, reason: str)
    """
    prompt = f"""
You are an AI assistant helping decide if Python analysis is needed for a data query.

USER'S QUESTION:
{user_question}

SQL QUERY THAT WAS EXECUTED:
{sql_code}

SQL RESULT PREVIEW:
{df_preview[:1000]}

DECISION REQUIRED:
Should we run additional Python analysis on these results, or is the SQL output sufficient to answer the user's question?

Python analysis is valuable for:
- Statistical analysis (correlations, regressions, predictions)
- Complex calculations (trends over time, growth rates, percentages)
- Multi-step transformations
- Grouping and aggregations not easily done in SQL
- Machine learning or predictive modeling

Python analysis is NOT needed for:
- Simple counts ("how many students")
- Direct lookups ("show me student X")
- Basic filters ("students with GPA > 3.0")
- Lists or tables that answer the question completely
- Single values that directly answer the question

Please respond with ONLY:
YES - if Python analysis would add meaningful insights
NO - if the SQL results already fully answer the question

Then on a new line, briefly explain your reasoning (1 sentence).
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.0
    )

    decision_text = response.choices[0].message.content.strip()
    lines = decision_text.split('\n', 1)
    decision = lines[0].strip().upper()
    reason = lines[1].strip() if len(lines) > 1 else "No reason provided"

    should_run = decision.startswith('YES')
    return should_run, reason

def ask_gpt_for_python(user_question, df_preview, client):
    """
    Tells GPT: "We have a pandas DataFrame named 'df' from the SQL result.
    Provide Python code for further analysis, no triple backticks."
    """
    prompt = f"""
We have a pandas DataFrame named 'df' from a SQL query result.
The user asked: {user_question}

Preview of df:
{df_preview[:1000]}  -- truncated

Write Python code that uses 'df' to further explore or summarize the data.

AVAILABLE LIBRARIES (already available):
- pandas (pd) - for data manipulation
- numpy (np) - for numerical operations
- matplotlib.pyplot (plt) - for charts
- tempfile, os - for file operations
- statsmodels - for regression (import as needed)
- scipy - for scientific computing (import as needed)
- scikit-learn (sklearn) - for ML (import as needed)

🚨 CRITICAL: CATEGORICAL VARIABLE HANDLING 🚨
STATSMODELS AND SKLEARN WILL FAIL IF YOU PASS STRING/OBJECT COLUMNS!

YOU MUST START EVERY ANALYSIS WITH THIS DATA PREPARATION BLOCK:
```
# MANDATORY: Check and convert data types
df_analysis = df.copy()

# Identify categorical columns (object/string types)
categorical_cols = df_analysis.select_dtypes(include=['object']).columns.tolist()

# Convert categorical to numeric using dummy variables
if categorical_cols:
    print(f"Converting categorical columns: {{categorical_cols}}")
    df_analysis = pd.get_dummies(df_analysis, columns=categorical_cols, drop_first=True)

# Handle missing values
df_analysis = df_analysis.dropna()

# Now df_analysis contains ONLY numeric columns - safe for regression/correlation
```

THIS IS NOT OPTIONAL. Every regression, correlation, or statistical analysis REQUIRES this block.

VISUALIZATIONS (when appropriate):
- Add charts for trends, distributions, comparisons, correlations
- Use matplotlib to create chart, save to temp file
- Charts enhance understanding for time series, demographics, patterns
- Don't create charts for simple counts or single values

IMPORTANT OUTPUT:
- Store final text output in a variable named 'result'
- If you create a chart, store the file path in a variable named 'result_image'
- Return ONLY the code (no triple backticks, no markdown)
- Make 'result' a readable string or formatted output

COMPLETE REGRESSION EXAMPLE (USE THIS PATTERN):
import statsmodels.api as sm
import tempfile
import os

# STEP 1: MANDATORY DATA PREP (ALWAYS DO THIS FIRST)
df_analysis = df.copy()
categorical_cols = df_analysis.select_dtypes(include=['object']).columns.tolist()
if categorical_cols:
    df_analysis = pd.get_dummies(df_analysis, columns=categorical_cols, drop_first=True)
df_analysis = df_analysis.dropna()

# STEP 2: Select target and features (now all numeric)
y = df_analysis['retention_flag']  # or whatever target
X = df_analysis.drop('retention_flag', axis=1)  # all other columns as features

# STEP 3: Run regression
X = sm.add_constant(X)
model = sm.OLS(y, X).fit()

# STEP 4: Format results
result = f\"\"\"## Regression Results

{{model.summary().as_text()}}

### Key Predictors:
The most significant predictors are shown in the coefficient table above.
Look for low p-values (< 0.05) to identify strong predictors.
\"\"\"

# STEP 5: Optional - create visualization
plt.figure(figsize=(12, 6))
coefficients = model.params[1:]  # exclude constant
coefficients.sort_values().plot(kind='barh')
plt.title('Feature Coefficients - Predictors of Retention')
plt.xlabel('Coefficient Value')
plt.tight_layout()

temp_dir = tempfile.gettempdir()
result_image = os.path.join(temp_dir, f'regression_{{hash(str(df.values.tobytes()))}}.png')
plt.savefig(result_image, format='png', bbox_inches='tight', dpi=100)
plt.close()

CORRELATION EXAMPLE (simpler, but still needs categorical handling):
# MANDATORY: Convert categorical columns first
df_analysis = df.copy()
categorical_cols = df_analysis.select_dtypes(include=['object']).columns.tolist()
if categorical_cols:
    df_analysis = pd.get_dummies(df_analysis, columns=categorical_cols, drop_first=True)
df_analysis = df_analysis.dropna()

# Now calculate correlation on all-numeric data
correlation = df_analysis.corr()
result = correlation.to_string()
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

def ask_gpt_for_explanation(sql_code, sql_result_str, py_code, py_result_str, client):
    """
    Combine everything into a final explanation for the user.
    Handles cases where Python analysis was skipped (py_code is None).
    """
    if py_code is None:
        # Python was skipped - explain SQL results only
        prompt = f"""
We executed a SQL query to answer the user's question.

SQL code generated:
{sql_code}

SQL results:
{sql_result_str}

Note: Python analysis was determined to be unnecessary for this straightforward query.

Provide a concise, friendly explanation of these SQL results for the user. Answer their question directly based on the data shown.

IMPORTANT OUTPUT FORMATTING:
- Include a markdown table when the data would benefit from tabular display
- Keep tables concise (top 10 rows max, or summarize if more)
- Use clear column headers
- Add a brief narrative explanation before or after the table
- For trend data, enrollment stats, demographic breakdowns, etc., tables are very helpful

Example with table:
## Enrollment Trends

Here are the enrollment numbers over the past 5 years:

| Year | Enrollment | Change |
|------|-----------|--------|
| 2020 | 5,234     | +2.3%  |
| 2021 | 5,456     | +4.2%  |
| 2022 | 5,589     | +2.4%  |

The data shows steady growth with an average increase of 3% per year.
"""
    else:
        # Normal flow - both SQL and Python were executed
        prompt = f"""
We had the following steps:

1) SQL code generated by GPT:
{sql_code}

2) Output from the SQL (or error):
{sql_result_str}

3) Python code:
{py_code}

4) Output from the Python code (or error):
{py_result_str}

Provide a concise, friendly explanation of these results for the user.

IMPORTANT OUTPUT FORMATTING:
- Include a markdown table when the data would benefit from tabular display
- Keep tables concise (top 10 rows max, or summarize if more)
- Use clear column headers
- Add narrative explanation to interpret the table
- Tables work great for: trends, comparisons, rankings, demographic breakdowns, statistical summaries
- If a visualization was generated (mentioned in Python output), note that it's displayed below

Example with table and visualization reference:
## Student Retention Analysis

Here's the retention rate breakdown by demographic group:

| Group | Retention Rate | Sample Size |
|-------|---------------|-------------|
| Group A | 87.5% | 1,234 |
| Group B | 82.3% | 987 |
| Group C | 91.2% | 756 |

The data reveals that Group C has the highest retention at 91.2%, while Group B shows the lowest at 82.3%. See the visualization below for a visual comparison.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

###############################################################################
# 5. GRADIO INTERFACE
###############################################################################

def ai_assistant(user_input, api_key_input):
    """
    1) GPT -> SQL code (fenced or unfenced).
    2) Remove fences, run the query.
    3) GPT -> Python code, remove fences, run the code.
    4) GPT -> final explanation.
    """
    # Use the API key from input if provided, otherwise use the default one
    active_api_key = api_key_input.strip() if api_key_input and api_key_input.strip() else DEFAULT_API_KEY

    # Check if API key is set
    if not active_api_key:
        message = """
❌ OpenAI API Key Not Set

To use this AI assistant, you need to set your OpenAI API key.

Steps to get started:
1. Get an API key from: https://platform.openai.com/api-keys
2. Enter it in the "OpenAI API Key" field above, OR
3. Set the environment variable:
   • Windows: set OPENAI_API_KEY=your_key_here
   • Mac/Linux: export OPENAI_API_KEY=your_key_here

For more information, see the README.md file.
"""
        return message, "Awaiting a valid API key to generate SQL details.", "Awaiting a valid API key to generate Python details.", gr.update(visible=False, value=None)

    # Create OpenAI client with the API key
    client = OpenAI(api_key=active_api_key)

    # RELEVANCE: Check if question is about the database data
    question_is_relevant, relevance_error = check_question_relevance(user_input, client)
    if not question_is_relevant:
        # Question is off-topic (general knowledge, unrelated to data)
        sql_details = (
            "### Question Rejected\n\n"
            "Your question was determined to be outside the scope of this database analysis tool.\n\n"
            "This interface is designed specifically for analyzing student enrollment, demographics, "
            "academic performance, and related higher education data.\n\n"
            "**Please ask questions that can be answered by querying the student database.**"
        )
        return relevance_error, sql_details, "Python analysis was not executed because the question was off-topic.", gr.update(visible=False, value=None)

    # SECURITY: Check user intent before generating SQL
    intent_is_safe, intent_warning = check_user_intent(user_input)
    if not intent_is_safe:
        # User is asking for a destructive operation
        sql_details = (
            "### Request Blocked Before SQL Generation\n\n"
            "The system detected that your request involves data modification or schema changes, "
            "which are not permitted in this read-only analysis interface.\n\n"
            "**Common phrases that trigger this protection:**\n"
            "- 'drop table/database/column'\n"
            "- 'delete records/rows/data'\n"
            "- 'update... to...'\n"
            "- 'insert into' (permanent tables)\n"
            "- 'alter table'\n"
            "- 'truncate table'\n\n"
            "**Try rephrasing to:**\n"
            "- 'Show me students with...'\n"
            "- 'What is the average...'\n"
            "- 'List all records where...'\n"
            "- 'Analyze trends in...'"
        )
        return intent_warning, sql_details, "Python analysis was not executed because the request was blocked.", gr.update(visible=False, value=None)

    # Step A: GPT for SQL
    raw_sql_code = ask_gpt_for_sql(user_input, client)
    # Clean out triple backticks or ```sql
    sql_code_clean = remove_sql_fences(raw_sql_code)

    # SECURITY: Validate SQL safety before execution
    is_safe, safety_error = validate_sql_safety(sql_code_clean)
    if not is_safe:
        # SQL failed safety validation
        explanation = f"🛡️ **Security Check Failed**\n\n{safety_error}\n\nThis interface only allows SELECT queries for data analysis and CREATE TEMPORARY TABLE for complex operations.\n\nPlease rephrase your question to request data analysis rather than data modification."
        sql_details = (
            "### Generated SQL (BLOCKED)\n"
            f"```sql\n{sql_code_clean}\n```\n\n"
            "### Security Validation Error\n"
            f"⚠️ {safety_error}\n\n"
            "**Allowed Operations:**\n"
            "- SELECT statements for querying data\n"
            "- CREATE TEMP TABLE for complex analysis\n\n"
            "**Blocked Operations:**\n"
            "- DROP, DELETE, UPDATE, INSERT (into permanent tables)\n"
            "- ALTER, TRUNCATE, GRANT, REVOKE\n"
            "- ATTACH, DETACH, PRAGMA, EXECUTE"
        )
        return explanation, sql_details, "Python analysis was not executed because the SQL was blocked for security reasons.", gr.update(visible=False, value=None)

    # Execute
    df_or_error = run_sql(sql_code_clean)
    if isinstance(df_or_error, str) and df_or_error.startswith("SQL Error:"):
        # The SQL failed
        explanation = f"SQL query failed. Please review the SQL details tab for more information.\n\n{df_or_error}"
        sql_details = (
            "### Generated SQL\n"
            f"```sql\n{sql_code_clean}\n```\n\n"
            "### Error\n"
            f"{df_or_error}"
        )
        return explanation, sql_details, "Python analysis was not executed because the SQL step failed.", gr.update(visible=False, value=None)

    # Build a short preview of the DataFrame
    if isinstance(df_or_error, pd.DataFrame):
        preview = df_or_error.head().to_string(index=False)
        cols_list = df_or_error.columns.tolist()
        df_preview_str = f"Columns: {cols_list}\nFirst 5 rows:\n{preview}"
    else:
        df_preview_str = str(df_or_error)

    # SMART DECISION: Ask GPT if Python analysis would add value
    should_run_python, decision_reason = should_run_python_analysis(
        user_input, sql_code_clean, df_preview_str, client
    )

    # Step B: Conditionally run Python analysis
    if should_run_python:
        raw_py_code = ask_gpt_for_python(user_input, df_preview_str, client)
        py_code_clean = remove_python_fences(raw_py_code)
        py_result, image_path = run_python_code(py_code_clean, df_or_error)
    else:
        # Skip Python - SQL results are sufficient
        py_code_clean = None
        py_result = f"Python analysis skipped.\n\nReason: {decision_reason}"
        image_path = None

    # Step C: GPT final explanation
    final_explanation = ask_gpt_for_explanation(
        sql_code_clean,
        df_preview_str,
        py_code_clean,
        py_result,
        client
    )

    summary_tab = (
        "### Your Question\n"
        f"{user_input}\n\n"
        "### Assistant Explanation\n"
        f"{final_explanation}"
    )

    sql_tab = (
        "### Generated SQL\n"
        f"```sql\n{sql_code_clean}\n```\n\n"
        "### SQL Result Preview\n"
        f"```\n{df_preview_str}\n```"
    )

    # Format Python tab - handle when Python was skipped
    if py_code_clean is None:
        python_tab = (
            "### Python Analysis: Not Required\n\n"
            f"{py_result}\n\n"
            "The SQL results were sufficient to answer your question, so additional Python analysis was not needed. "
            "This saves processing time and API costs for straightforward queries.\n\n"
            "**Python analysis is used for:**\n"
            "- Statistical calculations (correlations, regressions)\n"
            "- Complex transformations and aggregations\n"
            "- Trend analysis and predictions\n"
            "- Multi-step data processing"
        )
    else:
        python_tab = (
            "### Python Analysis Code\n"
            f"```python\n{py_code_clean}\n```\n\n"
            "### Python Output\n"
            f"```\n{py_result}\n```"
        )

    # Control image visibility based on whether visualization was generated
    if image_path:
        image_output = gr.update(visible=True, value=image_path)
    else:
        image_output = gr.update(visible=False, value=None)

    return summary_tab, sql_tab, python_tab, image_output

def main():
    """Launch the Gradio web interface for the AI assistant."""
    # Check if database exists, if not create it automatically
    if not os.path.exists(DB_PATH):
        print(f"\n{'='*70}")
        print("Database not found. Generating synthetic data...")
        print(f"{'='*70}")
        print("This will take about 30 seconds...\n")

        try:
            # Step 1: Create schema
            print("Step 1/2: Creating database schema...")
            create_ipeds_db_schema(DB_PATH)

            # Step 2: Generate synthetic data
            print("Step 2/2: Generating synthetic student data...")
            generate_stable_population_data()

            print(f"\n{'='*70}")
            print("✓ Database created successfully!")
            print(f"{'='*70}\n")
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"ERROR: Failed to create database: {str(e)}")
            print(f"{'='*70}\n")
            sys.exit(1)

    print(f"\nStarting Higher Education AI Analyst...")
    print(f"Using database: {DB_PATH}")
    print(f"OpenAI Model: gpt-4o")
    print("\nLaunching Gradio interface...")

    # Two-column layout with ChatGPT styling
    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    :root {
        color-scheme: dark;
    }

    /* Base styling */
    html, body {
        height: 100%;
        margin: 0;
        background: #0b1120 !important;
    }

    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: #0b1120 !important;
        color: #e2e8f0 !important;
        padding: 0 !important;
        max-width: 100% !important;
        min-height: 100vh !important;
        height: 100vh !important;
        overflow: hidden !important;
    }

    .gradio-container > .gr-blocks,
    .gradio-container .gr-blocks {
        height: 100% !important;
    }

    .gradio-container * {
        color: inherit;
    }

    /* Two-column layout */
    .two-column-container {
        display: grid !important;
        grid-template-columns: 420px 1fr !important;
        gap: 0 !important;
        height: 100% !important;
        min-height: 100% !important;
        align-items: stretch !important;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(8, 47, 73, 0.9)) !important;
    }

    /* Left column - input side */
    .left-column {
        background: rgba(17, 24, 39, 0.88) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.12) !important;
        padding: 32px 28px !important;
        overflow-y: auto !important;
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        max-height: 100% !important;
        backdrop-filter: blur(12px);
    }

    /* Right column - output side */
    .right-column {
        background: rgba(9, 17, 31, 0.82) !important;
        padding: 36px 32px !important;
        overflow-y: auto !important;
        height: 100% !important;
        max-height: 100% !important;
    }

    /* Header */
    .header-section {
        text-align: center !important;
        margin-bottom: 32px !important;
        padding-bottom: 24px !important;
        border-bottom: 1px solid rgba(148, 163, 184, 0.18) !important;
    }

    .header-section img {
        max-width: 60px !important;
        height: auto !important;
        margin: 0 auto 12px auto !important;
        filter: drop-shadow(0 8px 12px rgba(15, 23, 42, 0.45));
    }

    .header-section h1 {
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        color: #f8fafc !important;
        margin: 0 0 4px 0 !important;
    }

    .header-section p {
        font-size: 0.85rem !important;
        color: #94a3b8 !important;
        margin: 0 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }

    /* Question input */
    #question-input textarea {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        border-radius: 16px !important;
        color: #f8fafc !important;
        font-size: 1rem !important;
        padding: 18px 16px !important;
        min-height: 140px !important;
        resize: vertical !important;
        box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.05) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }

    #question-input textarea:focus {
        border-color: #38bdf8 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2) !important;
    }

    /* Example buttons */
    .examples-label {
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        color: #94a3b8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin: 24px 0 12px 0 !important;
    }

    .example-row {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 10px !important;
        margin-bottom: 18px !important;
    }

    .example-button button {
        background: rgba(30, 41, 59, 0.72) !important;
        border: 1px solid rgba(148, 163, 184, 0.16) !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
        font-size: 0.85rem !important;
        color: #e2e8f0 !important;
        cursor: pointer !important;
        transition: transform 0.15s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
        text-align: center !important;
        font-weight: 400 !important;
        width: 100% !important;
    }

    .example-button button:hover {
        background: rgba(59, 130, 246, 0.18) !important;
        border-color: rgba(59, 130, 246, 0.45) !important;
        box-shadow: 0 10px 22px -15px rgba(59, 130, 246, 0.6) !important;
        transform: translateY(-1px);
    }

    /* Submit button */
    button[variant="primary"] {
        background: linear-gradient(135deg, #6366f1, #38bdf8) !important;
        color: white !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        border: none !important;
        cursor: pointer !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 12px 22px -12px rgba(99, 102, 241, 0.7) !important;
        width: 100% !important;
        margin: 16px 0 20px 0 !important;
    }

    button[variant="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 28px -14px rgba(59, 130, 246, 0.75) !important;
    }

    /* API key section */
    .api-section {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(148, 163, 184, 0.12) !important;
        border-radius: 12px !important;
        padding: 18px !important;
        margin: 20px 0 !important;
        box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.05) !important;
    }

    #api-key-input input {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 8px !important;
        color: #e0f2fe !important;
        font-size: 0.85rem !important;
        padding: 12px 14px !important;
        font-family: 'SF Mono', Monaco, monospace !important;
    }

    #api-key-input input:focus {
        border-color: rgba(56, 189, 248, 0.6) !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2) !important;
    }

    .api-info {
        font-size: 0.75rem !important;
        color: #94a3b8 !important;
        margin-top: 10px !important;
    }

    .api-info a {
        color: #38bdf8 !important;
        text-decoration: none !important;
    }

    .api-info a:hover {
        text-decoration: underline !important;
    }

    /* Output results */
    .results-tabs {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
    }

    .results-tabs .tab-nav {
        gap: 8px !important;
        border: none !important;
        padding: 0 4px 12px 4px !important;
        background: transparent !important;
    }

    .results-tabs .tab-nav button {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
        color: #cbd5f5 !important;
        transition: background 0.2s ease, border-color 0.2s ease !important;
    }

    .results-tabs .tab-nav button[aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.22), rgba(56, 189, 248, 0.18)) !important;
        border-color: rgba(56, 189, 248, 0.5) !important;
        color: #e2e8f0 !important;
    }

    .results-tabs .tab-panels {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    .results-pane {
        background: rgba(10, 19, 35, 0.9) !important;
        border: 1px solid rgba(59, 130, 246, 0.45) !important;
        border-radius: 14px !important;
        padding: 20px !important;
        min-height: 200px !important;
        font-size: 0.9rem !important;
        line-height: 1.55 !important;
        color: #f8fafc !important;
        box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.06) !important;
        overflow: visible !important;
    }

    .results-pane pre {
        background: rgba(15, 23, 42, 0.88) !important;
        border-radius: 10px !important;
        padding: 12px !important;
        border: 1px solid rgba(148, 163, 184, 0.14) !important;
        font-size: 0.82rem !important;
    }

    .results-pane code {
        font-family: 'SF Mono', Monaco, 'Courier New', monospace !important;
    }

    /* About accordion */
    details {
        background: rgba(30, 41, 59, 0.72) !important;
        border: 1px solid rgba(148, 163, 184, 0.12) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-top: auto !important;
        box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.04) !important;
    }

    summary {
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        color: #cbd5f5 !important;
        cursor: pointer !important;
    }

    details[open] summary {
        margin-bottom: 12px !important;
        padding-bottom: 12px !important;
        border-bottom: 1px solid rgba(148, 163, 184, 0.18) !important;
    }

    details p, details li {
        color: #cbd5f5 !important;
        line-height: 1.6 !important;
        font-size: 0.85rem !important;
    }

    details h3 {
        color: #e0f2fe !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        margin: 12px 0 6px 0 !important;
    }

    details a {
        color: #38bdf8 !important;
        text-decoration: none !important;
    }

    details a:hover {
        text-decoration: underline !important;
    }

    /* Responsive - stack on small screens */
    @media (max-width: 1024px) {
        .gradio-container {
            height: auto !important;
            overflow: auto !important;
        }

        .two-column-container {
            grid-template-columns: 1fr !important;
            height: auto !important;
            min-height: auto !important;
        }

        .left-column {
            border-right: none !important;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12) !important;
            height: auto !important;
            max-height: none !important;
        }

        .results-pane {
            min-height: 180px !important;
            max-height: 300px !important;
        }

        .right-column {
            height: auto !important;
            max-height: none !important;
        }
    }
    """

    # Create elegant dark theme (kept minimal)
    theme = gr.themes.Base(
        primary_hue="stone",
        secondary_hue="stone",
        neutral_hue="stone",
    ).set(
        body_background_fill="*neutral_950",
        body_background_fill_dark="*neutral_950",
    )

    # Build two-column interface
    with gr.Blocks(theme=theme, css=custom_css, title="Higher Education AI Analyst") as demo:

        with gr.Row(elem_classes=["two-column-container"]):
            # LEFT COLUMN - Input side
            with gr.Column(elem_classes=["left-column"], scale=1):
                # Header
                gr.HTML("""
                    <div class="header-section">
                        <img src="https://raw.githubusercontent.com/mikeurl/Data-Analyst/claude/review-repo-structure-011CUqm6vjgy43VX5NmComtm/docs/logo.png"
                             alt="Higher Education AI Analyst">
                        <h1>Higher Education AI Analyst</h1>
                    </div>
                """)

                # Question input
                question_input = gr.Textbox(
                    lines=5,
                    label="Your Question",
                    placeholder="Ask a question about the data...",
                    elem_id="question-input",
                    interactive=True,
                    show_label=False
                )

                # Submit button
                submit_btn = gr.Button(
                    "Send",
                    variant="primary"
                )

                # Example prompts
                gr.HTML('<div class="examples-label">Examples</div>')

                with gr.Row(elem_classes=["example-row"]):
                    with gr.Column(scale=1, elem_classes=["example-button"]):
                        example1 = gr.Button("Retention by Demographics", size="sm")
                    with gr.Column(scale=1, elem_classes=["example-button"]):
                        example2 = gr.Button("GPA Trends", size="sm")

                with gr.Row(elem_classes=["example-row"]):
                    with gr.Column(scale=1, elem_classes=["example-button"]):
                        example3 = gr.Button("Graduation Statistics", size="sm")
                    with gr.Column(scale=1, elem_classes=["example-button"]):
                        example4 = gr.Button("Enrollment Distribution", size="sm")

                # API key section
                gr.HTML('<div class="api-section">')
                api_key_input = gr.Textbox(
                    lines=1,
                    label="OpenAI API Key (Optional)",
                    placeholder="sk-proj-...",
                    type="password",
                    elem_id="api-key-input",
                    interactive=True
                )
                gr.HTML('<p class="api-info">Optional if set via environment variable. <a href="https://platform.openai.com/api-keys" target="_blank">Get your key</a></p>')
                gr.HTML('</div>')

                # About section
                with gr.Accordion("About This Tool", open=False):
                    gr.Markdown("""
### How It Works

This tool employs a sophisticated three-step AI process:

1. **SQL Generation** — Translates your natural language question into a precise SQL query
2. **Local Execution** — Executes the query against the SQLite database
3. **Python Analysis** — Generates and runs Python code for deeper statistical analysis
4. **Intelligent Explanation** — Synthesizes results into clear, actionable insights

---

### Privacy & Data Handling

- All SQL execution and data analysis occurs **on the server**
- Only database schema and minimal data previews (5 rows) are sent to OpenAI's API
- This deployment uses **100% synthetic data** — no real student information
- Your API key is used only for your requests and is never stored

---

### Production Readiness

⚠️ **Important Notice:** This tool is designed for experimentation and educational purposes with synthetic data only.

Do not deploy with real student data without implementing:
- Comprehensive security measures
- Proper access controls
- FERPA compliance reviews
- Data governance policies

---

### Technical Details

- **Source Code:** [github.com/mikeurl/Data-Analyst](https://github.com/mikeurl/Data-Analyst)
- **AI Model:** OpenAI GPT-4o
- **Database:** SQLite with IPEDS-like schema
- **Framework:** Gradio + Python

---

### Attribution

*No Ball State University student data or institutional resources were used in this project.*

**Singulier Oblige** — Excellence in educational analytics
                    """)

            # RIGHT COLUMN - Output side
            with gr.Column(elem_classes=["right-column"], scale=2):
                with gr.Tabs(elem_classes=["results-tabs"]):
                    with gr.TabItem("Answer"):
                        answer_output = gr.Markdown(
                            "Ask a question to see the AI's explanation.",
                            elem_classes=["results-pane"],
                            elem_id="answer-pane"
                        )
                    with gr.TabItem("SQL Details"):
                        sql_output = gr.Markdown(
                            "SQL code and preview will appear here after you submit a question.",
                            elem_classes=["results-pane"],
                            elem_id="sql-pane"
                        )
                    with gr.TabItem("Python Details"):
                        python_output = gr.Markdown(
                            "Python analysis will appear here after you submit a question.",
                            elem_classes=["results-pane"],
                            elem_id="python-pane"
                        )

                # Visualization output (when Python generates charts)
                image_output = gr.Image(
                    label="Visualization",
                    visible=False,  # Hidden until visualization is generated
                    show_label=True,
                    type="filepath"
                )

        # Connect the submit button
        submit_btn.click(
            fn=ai_assistant,
            inputs=[question_input, api_key_input],
            outputs=[answer_output, sql_output, python_output, image_output]
        )

        # Also allow Enter key to submit (Enter will submit the form; multiline will use Shift+Enter for newline)
        question_input.submit(
            fn=ai_assistant,
            inputs=[question_input, api_key_input],
            outputs=[answer_output, sql_output, python_output, image_output]
        )

        # Connect example buttons to populate the question input using gr.update which is robust across gradio versions
        example1.click(
            fn=lambda: gr.update(value="What are the retention rates by race and ethnicity?"),
            inputs=None,
            outputs=question_input
        )
        example2.click(
            fn=lambda: gr.update(value="Show me the average GPA by class year"),
            inputs=None,
            outputs=question_input
        )
        example3.click(
            fn=lambda: gr.update(value="How many students graduated in each program?"),
            inputs=None,
            outputs=question_input
        )
        example4.click(
            fn=lambda: gr.update(value="What is the distribution of students across different terms?"),
            inputs=None,
            outputs=question_input
        )

    demo.launch(share=False, server_port=7860)

if __name__ == "__main__":
    main()
