import os
import gradio as gr
import pandas as pd
import openai

from validate_data import validate_student_data

# 1. Load your data
DATA_FILE = "synthetic_student_level_data.csv"
df = pd.read_csv(DATA_FILE)

# 2. Run validation script on the data
validation_issues = validate_student_data(DATA_FILE)

# 3. Set your OpenAI API key
openai.api_key = os.getenv("key")
if openai.api_key == "YOUR_OPENAI_KEY_HERE":
    raise ValueError("OpenAI API key is not set. Update the code or environment variable.")

def respond_to_user(user_input: str) -> str:
    """
    Gathers validation info and CIP distribution to build a system prompt,
    then includes the user's query as a separate 'user' message.
    Prints the entire messages array for debugging before calling the API.
    """

    # Summarize validation results
    if not validation_issues:
        validation_summary = "No data validation issues were found."
    else:
        validation_summary = "Validation issues found:\n- " + "\n- ".join(validation_issues)

    # Quick CIP distribution summary
    cip_dist = df["cip_code"].value_counts().to_dict()
    quick_stats = f"CIP code distribution: {cip_dist}"

    # Build messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant that helps interpret IPEDS Completions data.\n\n"
                f"Data Validation Summary:\n{validation_summary}\n\n"
                f"{quick_stats}\n\n"
                "Please answer the user's questions accurately and concisely."
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    # --- DEBUG PRINT OF ALL MESSAGES ---
    print("\n----- DEBUG: MESSAGES BEING SENT TO OPENAI -----")
    for idx, msg in enumerate(messages):
        print(f"Role: {msg['role']}")
        print(f"Content:\n{msg['content']}\n")
    print("----- END DEBUG -----\n")

    # Call the OpenAI ChatCompletion endpoint (old library syntax)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-4" if you have access
        messages=messages,
        temperature=0.2
    )

    # Extract the text from the response
    answer = response["choices"][0]["message"]["content"]
    return answer

def main():
    """
    Launch a Gradio interface to chat with the AI assistant.
    """
    iface = gr.Interface(
        fn=respond_to_user,
        inputs=gr.Textbox(lines=3, label="Ask your IPEDS Data Assistant"),
        outputs=gr.Textbox(),
        title="IPEDS Completions AI Assistant"
    )
    iface.launch()

if __name__ == "__main__":
    main()
