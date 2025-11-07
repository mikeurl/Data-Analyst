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

import openai
import gradio as gr
import pandas as pd

# Import database setup functions for auto-initialization
from create_ipeds_db_schema import create_ipeds_db_schema
from SyntheticDataforSchema2 import generate_stable_population_data

###############################################################################
# 1. CONFIGURATION
###############################################################################

DB_PATH = "ipeds_data.db"  # Path to your SQLite DB file.

# Get OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
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
    containing 'df' (the DataFrame from the SQL step) and 'pd' (pandas).
    Expects the code to store its final output in a variable named 'result'.
    Returns a string version of 'result'.
    """
    local_vars = {"df": df, "pd": pd}
    try:
        exec(py_code, {}, local_vars)
        output = local_vars.get("result", "No 'result' variable set.")
        return str(output)
    except Exception as e:
        return f"Python Error: {str(e)}"

###############################################################################
# 4. GPT INTERACTION
###############################################################################

def ask_gpt_for_sql(user_question):
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

Please provide ONLY the SQL code, no triple backticks. End with a semicolon.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # or "gpt-4" if you have access
        messages=[{"role": "system", "content": prompt}],
        temperature=0.0
    )
    return response["choices"][0]["message"]["content"]

def ask_gpt_for_python(user_question, df_preview):
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
Store final output in a variable named 'result'. Return ONLY the code (no triple backticks).
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.2
    )
    return response["choices"][0]["message"]["content"]

def ask_gpt_for_explanation(sql_code, sql_result_str, py_code, py_result_str):
    """
    Combine everything into a final explanation for the user.
    """
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
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.3
    )
    return response["choices"][0]["message"]["content"]

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
    # Use the API key from input if provided, otherwise use the global one
    active_api_key = api_key_input.strip() if api_key_input and api_key_input.strip() else openai.api_key

    # Check if API key is set
    if not active_api_key:
        return """
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

    # Temporarily set the API key for this request
    original_key = openai.api_key
    openai.api_key = active_api_key

    try:
        # Step A: GPT for SQL
        raw_sql_code = ask_gpt_for_sql(user_input)
        # Clean out triple backticks or ```sql
        sql_code_clean = remove_sql_fences(raw_sql_code)

        # Execute
        df_or_error = run_sql(sql_code_clean)
        if isinstance(df_or_error, str) and df_or_error.startswith("SQL Error:"):
            # The SQL failed
            explanation = f"SQL query failed:\n{df_or_error}\n\nSQL was:\n{sql_code_clean}"
            return explanation

        # Build a short preview of the DataFrame
        if isinstance(df_or_error, pd.DataFrame):
            preview = df_or_error.head().to_string(index=False)
            cols_list = df_or_error.columns.tolist()
            df_preview_str = f"Columns: {cols_list}\nFirst 5 rows:\n{preview}"
        else:
            df_preview_str = str(df_or_error)

        # Step B: GPT for Python
        raw_py_code = ask_gpt_for_python(user_input, df_preview_str)
        py_code_clean = remove_python_fences(raw_py_code)

        py_result = run_python_code(py_code_clean, df_or_error)

        # Step C: GPT final explanation
        final_explanation = ask_gpt_for_explanation(
            sql_code_clean,
            df_preview_str,
            py_code_clean,
            py_result
        )

        return (
            f"[SQL CODE]\n{sql_code_clean}\n\n"
            f"[SQL RESULT PREVIEW]\n{df_preview_str}\n\n"
            f"[PYTHON CODE]\n{py_code_clean}\n\n"
            f"[PYTHON RESULT]\n{py_result}\n\n"
            f"[GPT EXPLANATION]\n{final_explanation}"
        )
    finally:
        # Restore original API key
        openai.api_key = original_key

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

    # Modern premium AI interface CSS
    custom_css = """
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global background gradient */
    .gradio-container {
        font-family: 'Inter', sans-serif !important;
        background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%) !important;
        padding: 40px !important;
    }

    /* Header row styling */
    #header-row {
        margin-bottom: 40px !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Logo container (left 20%) */
    #logo-container {
        width: 20% !important;
        display: flex !important;
        align-items: center !important;
    }

    #logo-container img {
        max-width: 180px !important;
        height: auto !important;
        filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3)) !important;
    }

    /* Title box (right 80%) - glassmorphism */
    .title-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
        padding: 24px 32px !important;
        text-align: right !important;
        width: 80% !important;
        margin-left: auto !important;
    }

    .title-box h1 {
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        margin: 0 !important;
        letter-spacing: 0.5px !important;
    }

    .title-box h2 {
        font-size: 1.25rem !important;
        font-weight: 400 !important;
        color: rgba(255, 255, 255, 0.9) !important;
        margin: 0.5rem 0 0 0 !important;
        opacity: 0.9 !important;
    }

    .title-box p {
        font-size: 0.95rem !important;
        color: rgba(255, 255, 255, 0.7) !important;
        margin: 0.75rem 0 0 0 !important;
    }

    /* ALL textarea and input backgrounds - CORRECTED COLORS */
    #question-input textarea,
    #api-key-input input,
    #output-results textarea,
    input[type="password"],
    textarea {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(100, 116, 139, 0.3) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease !important;
    }

    #question-input textarea::placeholder,
    #api-key-input input::placeholder,
    input::placeholder,
    textarea::placeholder {
        opacity: 0.5 !important;
        color: rgba(255, 255, 255, 0.5) !important;
    }

    #question-input textarea:focus,
    #api-key-input input:focus,
    #output-results textarea:focus,
    input:focus,
    textarea:focus {
        outline: 2px solid #60a5fa !important;
        outline-offset: 2px !important;
        border-color: transparent !important;
        box-shadow: none !important;
    }

    /* Question textarea - not dominating */
    #question-input textarea {
        min-height: 150px !important;
        max-height: 200px !important;
    }

    /* Labels */
    label {
        font-weight: 500 !important;
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.875rem !important;
        margin-bottom: 8px !important;
        display: block !important;
    }

    /* Submit button with gradient */
    .submit-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        padding: 12px 32px !important;
        font-size: 1rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
        margin-top: 16px !important;
        width: 100% !important;
    }

    .submit-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }

    /* API key section - less prominent */
    #api-key-section {
        margin-top: 20px !important;
        padding-top: 20px !important;
        border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    #api-key-section label {
        font-size: 0.8rem !important;
        color: rgba(255, 255, 255, 0.6) !important;
    }

    .api-info {
        font-size: 0.75rem !important;
        color: rgba(255, 255, 255, 0.5) !important;
        margin-top: 4px !important;
    }

    .api-info a {
        color: #60a5fa !important;
        text-decoration: none !important;
    }

    .api-info a:hover {
        text-decoration: underline !important;
    }

    /* Example chips - UPDATED COLORS */
    .example-chips {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
        margin-top: 20px !important;
    }

    .example-chip {
        background: rgba(79, 70, 229, 0.3) !important;
        border: 1px solid rgba(79, 70, 229, 0.5) !important;
        border-radius: 20px !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
        color: rgba(255, 255, 255, 0.8) !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        display: inline-block !important;
    }

    .example-chip:hover {
        background: rgba(79, 70, 229, 0.5) !important;
        border-color: rgba(79, 70, 229, 0.7) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }

    /* Output results specific styling */
    #output-results textarea {
        color: rgba(226, 232, 240, 0.9) !important;
        font-family: 'Monaco', 'Courier New', monospace !important;
        font-size: 0.875rem !important;
        line-height: 1.6 !important;
        min-height: 400px !important;
    }

    /* Accordion styling - CONSISTENT WITH ANALYSIS RESULTS */
    details {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(100, 116, 139, 0.3) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-top: 20px !important;
        backdrop-filter: blur(10px) !important;
    }

    summary {
        font-weight: 500 !important;
        color: rgba(226, 232, 240, 0.9) !important;
        cursor: pointer !important;
        font-size: 0.95rem !important;
    }

    summary:hover {
        color: #60a5fa !important;
    }

    details p, details ul, details li {
        color: rgba(226, 232, 240, 0.9) !important;
        line-height: 1.6 !important;
    }

    details h3 {
        color: rgba(226, 232, 240, 0.95) !important;
    }

    /* Links */
    a {
        color: #60a5fa !important;
        text-decoration: none !important;
    }

    a:hover {
        text-decoration: underline !important;
    }

    /* Loading spinner */
    .loading {
        opacity: 0.6 !important;
        pointer-events: none !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px !important;
    }

    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.2) !important;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(102, 126, 234, 0.3) !important;
        border-radius: 5px !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(102, 126, 234, 0.5) !important;
    }

    /* Spacing utilities */
    .section-spacing {
        margin-bottom: 20px !important;
    }

    /* Override Gradio button defaults - PERFECT BUTTON */
    button[variant="primary"],
    .submit-button,
    button.primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 16px 48px !important;
        border-radius: 8px !important;
        border: none !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
        margin-top: 16px !important;
        font-size: 1rem !important;
        letter-spacing: 0.3px !important;
    }

    button[variant="primary"]:hover,
    .submit-button:hover,
    button.primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4) !important;
    }

    button[variant="primary"]:active,
    .submit-button:active {
        transform: translateY(0) !important;
    }

    /* Component spacing */
    #question-input,
    #api-key-input,
    button[variant="primary"] {
        margin-bottom: 16px !important;
    }
    """

    # Create elegant dark theme
    theme = gr.themes.Base(
        primary_hue="stone",
        secondary_hue="stone",
        neutral_hue="stone",
    ).set(
        body_background_fill="*neutral_950",
        body_background_fill_dark="*neutral_950",
    )

    # Build modern premium AI interface
    with gr.Blocks(theme=theme, css=custom_css, title="Higher Education AI Analyst") as demo:

        # HEADER: Logo (left 20%) + Title Box (right 80%)
        with gr.Row(elem_id="header-row"):
            # Logo container
            with gr.Column(scale=2):
                gr.HTML("""
                    <div id="logo-container">
                        <img src="https://raw.githubusercontent.com/mikeurl/Data-Analyst/claude/review-repo-structure-011CUqm6vjgy43VX5NmComtm/docs/logo.png"
                             alt="Singulier Oblige">
                    </div>
                """)

            # Title box with glassmorphism
            with gr.Column(scale=8):
                gr.HTML("""
                    <div class="title-box">
                        <h1>Singulier Oblige</h1>
                        <h2>Higher Education AI Analyst</h2>
                        <p>Transform your questions into insights. Ask in plain language, receive intelligent analysis.</p>
                    </div>
                """)

        # Question input
        question_input = gr.Textbox(
            lines=6,
            label="Ask Your Question",
            placeholder="e.g., 'Show me retention rates by race/ethnicity' or 'What's the average GPA by class year?'",
            elem_id="question-input"
        )

        # Example query chips
        gr.HTML("""
            <div class="example-chips">
                <span class="example-chip" onclick="document.querySelector('#question-input textarea').value='What are the retention rates by race and ethnicity?'">📊 Retention by Demographics</span>
                <span class="example-chip" onclick="document.querySelector('#question-input textarea').value='Show me the average GPA by class year'">📈 GPA Trends</span>
                <span class="example-chip" onclick="document.querySelector('#question-input textarea').value='How many students graduated in each program?'">🎓 Graduation Stats</span>
                <span class="example-chip" onclick="document.querySelector('#question-input textarea').value='What is the distribution of students across different terms?'">📅 Enrollment Distribution</span>
            </div>
        """)

        # API Key section
        api_key_input = gr.Textbox(
            lines=1,
            label="OpenAI API Key (Optional)",
            placeholder="sk-proj-...",
            type="password",
            elem_id="api-key-input"
        )
        gr.HTML('<p class="api-info">Leave blank if set via environment variable. Get your API key at <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a></p>')

        # Submit button
        submit_btn = gr.Button(
            "🔍 Analyze Data",
            variant="primary",
            size="lg"
        )

        # Output section
        output = gr.Textbox(
            label="📄 Analysis Results",
            lines=20,
            max_lines=50,
            show_copy_button=True,
            elem_id="output-results"
        )

        # About section
        with gr.Accordion("ℹ️ About This Tool", open=False):
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

        # Connect the button
        submit_btn.click(
            fn=ai_assistant,
            inputs=[question_input, api_key_input],
            outputs=output
        )

        # Also allow Enter key to submit
        question_input.submit(
            fn=ai_assistant,
            inputs=[question_input, api_key_input],
            outputs=output
        )

    demo.launch(share=False, server_port=7860)

if __name__ == "__main__":
    main()
