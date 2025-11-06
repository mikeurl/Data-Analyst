---
title: Higher Education AI Analyst
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
---

# Higher Education AI Analyst

Ask questions about higher education data in natural language. This tool uses AI to convert your questions into SQL queries and Python analysis, then explains the results in plain English.

## How to Use

1. **Get an OpenAI API Key**: Visit [platform.openai.com/api-keys](https://platform.openai.com/api-keys) to create an API key
2. **Enter your API key** in the password field (your key is never stored)
3. **Ask a question** in natural language about student data
4. **View the analysis** - see the SQL generated, the data results, and the AI explanation

## Example Questions

- "What are the retention rates by race and ethnicity?"
- "Show me the average GPA by class year"
- "How many students graduated in each program?"
- "What's the distribution of students across different terms?"

## How It Works

This tool uses a three-step AI process:

1. **SQL Generation**: Converts your question into a SQL query based on the database schema
2. **Local Execution**: Runs the query against a SQLite database
3. **Python Analysis**: Generates and executes Python code for further analysis
4. **Explanation**: Provides a human-readable summary of the results

## Privacy & Data

- This instance uses **100% synthetic data** - no real student information
- Only the database schema and small data previews (5 rows) are sent to OpenAI's API
- All SQL execution and data analysis happens on the server
- Your API key is used only for your requests and is not stored

## Production Readiness

⚠️ **This tool is not production-ready.** It is designed for experimentation and educational purposes with synthetic data only.

Do not use with real student data without implementing proper security measures, access controls, and compliance reviews.

## Source Code

GitHub Repository: [github.com/mikeurl/Data-Analyst](https://github.com/mikeurl/Data-Analyst)

## Note

No Ball State student data or resources were used in this project.

## License

See the GitHub repository for license information.
