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

Please provide ONLY the SQL code, no triple backticks. End with a semicolon.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content

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
Store final output in a variable named 'result'. Return ONLY the code (no triple backticks).
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

    # Create OpenAI client with the API key
    client = OpenAI(api_key=active_api_key)

    # Step A: GPT for SQL
    raw_sql_code = ask_gpt_for_sql(user_input, client)
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
    raw_py_code = ask_gpt_for_python(user_input, df_preview_str, client)
    py_code_clean = remove_python_fences(raw_py_code)

    py_result = run_python_code(py_code_clean, df_or_error)

    # Step C: GPT final explanation
    final_explanation = ask_gpt_for_explanation(
        sql_code_clean,
        df_preview_str,
        py_code_clean,
        py_result,
        client
    )

    return (
        f"[SQL CODE]\n{sql_code_clean}\n\n"
        f"[SQL RESULT PREVIEW]\n{df_preview_str}\n\n"
        f"[PYTHON CODE]\n{py_code_clean}\n\n"
        f"[PYTHON RESULT]\n{py_result}\n\n"
        f"[GPT EXPLANATION]\n{final_explanation}"
    )

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

    # ChatGPT-style interface - clean, minimal, focused
    custom_css = """
    /* ChatGPT aesthetic - clean and minimal */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* Clean light background like ChatGPT */
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: #f9fafb !important;
        padding: 0 !important;
        min-height: 100vh !important;
    }

    /* Centered column like ChatGPT */
    .main-wrapper {
        max-width: 768px !important;
        margin: 0 auto !important;
        padding: 24px 16px !important;
    }

    /* Clean header */
    .header-section {
        text-align: center !important;
        padding: 32px 0 24px 0 !important;
        border-bottom: 1px solid #e5e7eb !important;
        margin-bottom: 32px !important;
    }

    .header-section img {
        max-width: 48px !important;
        height: auto !important;
        margin: 0 auto 16px auto !important;
        opacity: 0.9 !important;
    }

    .header-section h1 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #111827 !important;
        margin: 0 !important;
    }

    .header-section p {
        font-size: 0.875rem !important;
        color: #6b7280 !important;
        margin: 8px 0 0 0 !important;
    }

    /* ChatGPT-style input box using wrapper class */
    .question-input-wrapper {
        margin-bottom: 24px !important;
    }

    .question-input-wrapper label {
        display: none !important;
    }

    /* Target Gradio's actual textarea element */
    .question-input-wrapper .gradio-textbox textarea,
    .question-input-wrapper textarea {
        background: white !important;
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
        color: #111827 !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        padding: 16px !important;
        min-height: 120px !important;
        resize: vertical !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease !important;
    }

    .question-input-wrapper .gradio-textbox textarea::placeholder,
    .question-input-wrapper textarea::placeholder {
        color: #9ca3af !important;
    }

    .question-input-wrapper .gradio-textbox textarea:focus,
    .question-input-wrapper textarea:focus {
        border-color: #10a37f !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1) !important;
    }

    /* Example prompts - minimal chips */
    .examples-wrapper {
        margin-bottom: 24px !important;
    }

    .examples-label {
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        color: #6b7280 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 12px !important;
    }

    .example-chips {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        margin-bottom: 0 !important;
    }

    /* Target Gradio buttons with example-chip class */
    .example-chip button {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 0.875rem !important;
        color: #374151 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        text-align: center !important;
        font-weight: 400 !important;
        min-width: 150px !important;
    }

    .example-chip button:hover {
        background: #f9fafb !important;
        border-color: #10a37f !important;
        color: #111827 !important;
    }

    /* ChatGPT green button */
    button[variant="primary"] {
        background: #10a37f !important;
        color: white !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        width: 100% !important;
        margin-bottom: 16px !important;
    }

    button[variant="primary"]:hover {
        background: #0d8f6f !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }

    button[variant="primary"]:active {
        background: #0b7a5f !important;
    }

    /* API key section - minimal */
    .api-wrapper {
        background: #f3f4f6 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin-bottom: 24px !important;
    }

    .api-key-input-wrapper label {
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        color: #6b7280 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 8px !important;
    }

    .api-key-input-wrapper input,
    .api-key-input-wrapper .gradio-textbox input {
        background: white !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        color: #111827 !important;
        font-size: 0.875rem !important;
        padding: 10px 12px !important;
        font-family: 'SF Mono', Monaco, monospace !important;
    }

    .api-key-input-wrapper input:focus,
    .api-key-input-wrapper .gradio-textbox input:focus {
        border-color: #10a37f !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1) !important;
    }

    .api-info {
        font-size: 0.75rem !important;
        color: #6b7280 !important;
        margin-top: 8px !important;
        line-height: 1.5 !important;
    }

    .api-info a {
        color: #10a37f !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }

    .api-info a:hover {
        text-decoration: underline !important;
    }

    /* Results section - clean */
    #output-results {
        margin-top: 32px !important;
    }

    #output-results label {
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        color: #111827 !important;
        margin-bottom: 12px !important;
    }

    #output-results textarea {
        background: white !important;
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
        color: #111827 !important;
        font-family: 'SF Mono', Monaco, 'Courier New', monospace !important;
        font-size: 0.875rem !important;
        line-height: 1.7 !important;
        padding: 16px !important;
        min-height: 400px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }

    /* About section - minimal accordion */
    details {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin-top: 32px !important;
    }

    summary {
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        color: #374151 !important;
        cursor: pointer !important;
        list-style: none !important;
    }

    summary::-webkit-details-marker {
        display: none !important;
    }

    summary:hover {
        color: #111827 !important;
    }

    details[open] summary {
        margin-bottom: 16px !important;
        padding-bottom: 12px !important;
        border-bottom: 1px solid #f3f4f6 !important;
    }

    details p, details li {
        color: #4b5563 !important;
        line-height: 1.6 !important;
        font-size: 0.875rem !important;
    }

    details h3 {
        color: #111827 !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        margin: 16px 0 8px 0 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.025em !important;
    }

    details h3:first-of-type {
        margin-top: 0 !important;
    }

    details a {
        color: #10a37f !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }

    details a:hover {
        text-decoration: underline !important;
    }

    /* Clean scrollbar */
    ::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }

    ::-webkit-scrollbar-track {
        background: transparent !important;
    }

    ::-webkit-scrollbar-thumb {
        background: #d1d5db !important;
        border-radius: 4px !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #9ca3af !important;
    }

    /* Responsive */
    @media (max-width: 640px) {
        .main-wrapper {
            padding: 16px 12px !important;
        }

        .example-chips {
            grid-template-columns: 1fr !important;
        }
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

    # Build clean ChatGPT-style interface
    with gr.Blocks(theme=theme, css=custom_css, title="Higher Education AI Analyst") as demo:

        # Clean header with logo and title
        gr.HTML("""
            <div class="header-section">
                <img src="https://raw.githubusercontent.com/mikeurl/Data-Analyst/claude/review-repo-structure-011CUqm6vjgy43VX5NmComtm/docs/logo.png"
                     alt="Singulier Oblige">
                <h1>Higher Education AI Analyst</h1>
                <p>by Singulier Oblige</p>
            </div>
        """)

        # Question input
        question_input = gr.Textbox(
            lines=4,
            label="",
            placeholder="Ask a question about the data...",
            elem_classes=["question-input-wrapper"],
            interactive=True
        )

        # Example prompts using proper Gradio buttons
        gr.HTML('<div class="examples-wrapper"><div class="examples-label">Examples</div>')

        with gr.Row(elem_classes=["example-chips"]):
            example1 = gr.Button("Retention by Demographics", elem_classes=["example-chip"])
            example2 = gr.Button("GPA Trends", elem_classes=["example-chip"])
            example3 = gr.Button("Graduation Statistics", elem_classes=["example-chip"])
            example4 = gr.Button("Enrollment Distribution", elem_classes=["example-chip"])

        gr.HTML('</div>')

        # Submit button
        submit_btn = gr.Button(
            "Send",
            variant="primary"
        )

        # API key section
        gr.HTML('<div class="api-wrapper">')
        api_key_input = gr.Textbox(
            lines=1,
            label="OpenAI API Key (Optional)",
            placeholder="sk-proj-...",
            type="password",
            elem_classes=["api-key-input-wrapper"],
            interactive=True
        )
        gr.HTML('<p class="api-info">Optional if set via environment variable. <a href="https://platform.openai.com/api-keys" target="_blank">Get your key</a></p>')
        gr.HTML('</div>')

        # Results
        output = gr.Textbox(
            label="Results",
            lines=20,
            max_lines=50,
            show_copy_button=True,
            elem_id="output-results"
        )

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

        # Connect the submit button
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

        # Connect example buttons to populate the question input
        example1.click(
            lambda: "What are the retention rates by race and ethnicity?",
            outputs=question_input
        )
        example2.click(
            lambda: "Show me the average GPA by class year",
            outputs=question_input
        )
        example3.click(
            lambda: "How many students graduated in each program?",
            outputs=question_input
        )
        example4.click(
            lambda: "What is the distribution of students across different terms?",
            outputs=question_input
        )

    demo.launch(share=False, server_port=7860)

if __name__ == "__main__":
    main()
