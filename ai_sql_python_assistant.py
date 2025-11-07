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

    # Custom CSS for modern, elegant design matching the logo
    custom_css = """
    /* Import elegant fonts */
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@300;400;600&family=Inter:wght@300;400;500;600&display=swap');

    /* Global styles */
    .gradio-container {
        font-family: 'Inter', sans-serif !important;
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%) !important;
    }

    /* Logo and header section */
    .logo-container {
        text-align: center;
        padding: 2rem 0 1rem 0;
        background: transparent;
    }

    .logo-container img {
        max-width: 200px;
        height: auto;
        margin: 0 auto;
        filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));
    }

    .tagline {
        font-family: 'Crimson Pro', serif !important;
        font-size: 1.5rem !important;
        font-weight: 300 !important;
        color: #f5f3ed !important;
        text-align: center !important;
        margin: 1.5rem 0 0.5rem 0 !important;
        letter-spacing: 0.5px !important;
    }

    .subtitle {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        color: #b8b5a8 !important;
        text-align: center !important;
        margin: 0 0 2rem 0 !important;
        font-weight: 300 !important;
    }

    /* Main container */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }

    /* Input section card */
    .input-card {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(245, 243, 237, 0.1) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }

    /* Labels */
    label {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        color: #f5f3ed !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.3px !important;
        margin-bottom: 0.5rem !important;
    }

    /* Input fields */
    input, textarea {
        background: rgba(26, 31, 46, 0.8) !important;
        border: 1px solid rgba(245, 243, 237, 0.15) !important;
        border-radius: 8px !important;
        color: #f5f3ed !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease !important;
    }

    input:focus, textarea:focus {
        border-color: rgba(212, 175, 106, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(212, 175, 106, 0.1) !important;
        outline: none !important;
    }

    /* Buttons */
    .primary-button {
        background: linear-gradient(135deg, #d4af6a 0%, #b89656 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #1a1f2e !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.875rem 2rem !important;
        font-size: 1rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(212, 175, 106, 0.3) !important;
    }

    .primary-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(212, 175, 106, 0.4) !important;
    }

    /* Output area */
    .output-container {
        background: rgba(26, 31, 46, 0.6) !important;
        border: 1px solid rgba(245, 243, 237, 0.1) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin-top: 1.5rem !important;
        font-family: 'Monaco', 'Courier New', monospace !important;
        color: #f5f3ed !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Examples section */
    .examples-container {
        margin-top: 2rem !important;
    }

    .example-item {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(245, 243, 237, 0.08) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        color: #b8b5a8 !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }

    .example-item:hover {
        background: rgba(212, 175, 106, 0.1) !important;
        border-color: rgba(212, 175, 106, 0.3) !important;
        color: #f5f3ed !important;
    }

    /* Accordion */
    .accordion {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(245, 243, 237, 0.08) !important;
        border-radius: 12px !important;
        margin-top: 2rem !important;
    }

    .accordion summary {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        color: #f5f3ed !important;
        padding: 1rem 1.5rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }

    .accordion summary:hover {
        color: #d4af6a !important;
    }

    .accordion-content {
        color: #b8b5a8 !important;
        padding: 0 1.5rem 1.5rem 1.5rem !important;
        line-height: 1.7 !important;
    }

    /* Links */
    a {
        color: #d4af6a !important;
        text-decoration: none !important;
        transition: all 0.3s ease !important;
    }

    a:hover {
        color: #e5c07a !important;
        text-decoration: underline !important;
    }

    /* Headings in markdown */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Crimson Pro', serif !important;
        color: #f5f3ed !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(26, 31, 46, 0.3);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(212, 175, 106, 0.3);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(212, 175, 106, 0.5);
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

    # Build interface using Blocks for complete control
    with gr.Blocks(theme=theme, css=custom_css, title="Higher Education AI Analyst") as demo:
        # Logo and header
        gr.HTML("""
            <div class="logo-container">
                <img src="file/docs/logo.png" alt="Singulier Oblige">
            </div>
        """)

        gr.Markdown(
            "<div class='tagline'>Higher Education AI Analyst</div>"
        )

        gr.Markdown(
            "<div class='subtitle'>Transform your questions into insights. Ask in plain language, receive intelligent analysis.</div>"
        )

        gr.Markdown(
            "<div style='text-align: center; color: #b8b5a8; font-size: 0.85rem; margin-bottom: 2rem;'>Get your API key from <a href='https://platform.openai.com/api-keys' target='_blank'>platform.openai.com/api-keys</a></div>"
        )

        # Main input area
        with gr.Row():
            with gr.Column(scale=1):
                question_input = gr.Textbox(
                    lines=4,
                    label="Your Question",
                    placeholder="e.g., 'Show me retention rates by race/ethnicity' or 'What's the average GPA by class year?'"
                )

                api_key_input = gr.Textbox(
                    lines=1,
                    label="OpenAI API Key",
                    placeholder="sk-proj-...",
                    type="password",
                    info="Optional if set via environment variable"
                )

                submit_btn = gr.Button(
                    "Analyze Data",
                    variant="primary",
                    size="lg"
                )

        # Output area
        with gr.Row():
            output = gr.Textbox(
                label="Analysis Results",
                lines=20,
                max_lines=50,
                show_copy_button=True
            )

        # Examples section
        gr.Markdown("<div style='margin-top: 2rem; margin-bottom: 1rem;'><h3 style='color: #f5f3ed; font-family: Crimson Pro, serif; font-weight: 400; font-size: 1.2rem;'>Example Questions</h3></div>")

        gr.Examples(
            examples=[
                ["What are the retention rates by race and ethnicity?", ""],
                ["Show me the average GPA by class year", ""],
                ["How many students graduated in each program?", ""],
                ["What's the distribution of students across different terms?", ""]
            ],
            inputs=[question_input, api_key_input],
            outputs=output,
            fn=ai_assistant,
            cache_examples=False
        )

        # About section with elegant styling
        with gr.Accordion("About This Tool", open=False):
            gr.Markdown("""
<div class='accordion-content'>

### How It Works

This tool employs a sophisticated three-step AI process:

1. **SQL Generation** — Translates your natural language question into a precise SQL query based on the database schema
2. **Local Execution** — Executes the query against your SQLite database
3. **Python Analysis** — Generates and runs Python code for deeper statistical analysis
4. **Intelligent Explanation** — Synthesizes results into clear, actionable insights

---

### Privacy & Data Handling

- All SQL execution and data analysis occurs **locally on your server**
- Only database schema and minimal data previews (5 rows) are transmitted to OpenAI's API
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

**Source Code:** [github.com/mikeurl/Data-Analyst](https://github.com/mikeurl/Data-Analyst)
**Model:** OpenAI GPT-4o
**Database:** SQLite with IPEDS-like schema
**Framework:** Gradio + Python

---

### Attribution

*No Ball State University student data or institutional resources were used in this project.*

**Singulier Oblige** — Excellence in educational analytics

</div>
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
