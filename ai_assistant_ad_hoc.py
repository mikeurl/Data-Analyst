import os
import re
import openai
import gradio as gr
import pandas as pd

#####################
# 1. Data + Settings
#####################

DATA_FILE = "synthetic_student_level_data.csv"
df = pd.read_csv(DATA_FILE)

openai.api_key = os.getenv("key")
if openai.api_key == "YOUR_OPENAI_KEY_HERE":
    raise ValueError("OpenAI API key not set.")

# We'll capture the DataFrame columns so GPT knows what's actually available
column_list = list(df.columns)
columns_str = ", ".join(column_list)

##############################
# 2. Utility: Clean Code Fences
##############################
def extract_code_block(text):
    """
    Searches for a code block enclosed in triple backticks (```).
    If found, returns only the Python code inside.
    Otherwise, returns the original text.
    """
    # Regex to capture text between ```...``` or ```python...```
    match = re.search(r"```(?:python)?\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        # If there's no fenced block, just strip any standalone backticks
        # in case GPT returned them inline
        return text.replace("```", "")

##############################
# 3. Utility: Safe Exec
##############################
def safe_exec_python(code_str, data_df):
    """
    Minimal function to safely execute Python code that references 'df'.
    DO NOT USE IN PROD as-is! This is just for demonstration.
    """
    local_vars = {"df": data_df, "pd": pd}
    try:
        exec(code_str, {}, local_vars)
        # Expect the code to store the final output in 'result'
        result = local_vars.get("result", "No 'result' variable set.")
        return str(result)
    except Exception as e:
        return f"Error executing code: {e}"

##############################
# 4. Main Chat Function
##############################
def respond_to_user(user_input):
    """
    We'll do a two-step approach:
      A) GPT tries to interpret user input and produce Python code referencing df.
      B) We run that code locally, then ask GPT to explain the result.
    """

    # STEP A: GPT writes code to answer the user's question
    step1_prompt = f"""
You are a data analysis assistant working with a pandas DataFrame named 'df'.
The DataFrame has these columns: {columns_str}

The user wants the following:
\"\"\"{user_input}\"\"\"

Write Python code that does the following:
1. Summarizes or filters the data as requested by the user.
2. You may import pandas as pd if needed.
3. Store the final output in a variable called 'result'.

Rules:
- ONLY reference 'df', 'pd', or standard Python (no external system calls).
- End with a line like: result = <expression>
- If you need to generate a table, return it as a pandas DataFrame or Series in 'result'.
- If uncertain, do your best. We'll handle errors in a second step.
"""

    step1_response = openai.ChatCompletion.create(
        model="gpt-4o",   # or "gpt-3.5-turbo" if you don't have GPT-4
        messages=[{"role": "system", "content": step1_prompt}],
        temperature=0.0
    )
    code_snippet = step1_response["choices"][0]["message"]["content"]

    # CLEAN out any triple-backtick fences
    code_snippet_clean = extract_code_block(code_snippet)

    # STEP B: Execute the snippet and pass the result back to GPT for explanation
    result_str = safe_exec_python(code_snippet_clean, df)

    step2_prompt = f"""
You generated the following Python code:

{code_snippet}

We cleaned it of any triple backticks before running, resulting in:

{code_snippet_clean}

Execution produced this output (as a string):

{result_str}

Now explain these results to the user in a concise, friendly way.
If there's an error message, explain what might be wrong and how to fix it.
"""

    step2_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": step2_prompt}],
        temperature=0.2
    )

    final_answer = step2_response["choices"][0]["message"]["content"]

    # Return a combined result:
    return (
        f"[GPT-4's Proposed Python Code]:\n{code_snippet}\n\n"
        f"[Cleaned Code Snippet for Execution]:\n{code_snippet_clean}\n\n"
        f"[Execution Output or Error]:\n{result_str}\n\n"
        f"[GPT-4's Explanation]:\n{final_answer}"
    )

##############################
# 5. Gradio UI
##############################
def main():
    iface = gr.Interface(
        fn=respond_to_user,
        inputs=gr.Textbox(label="Ask your Completions Data Assistant"),
        outputs=gr.Textbox(label="AI Response"),
        title="Ad-hoc IPEDS Query Demo (GPT-4) - Cleaned Code"
    )
    iface.launch()

if __name__ == "__main__":
    main()
