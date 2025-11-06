# IPEDS Data Analysis Toolkit - Windows Setup Guide

Complete step-by-step instructions for setting up and running the IPEDS Data Analysis Toolkit on Windows.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Scripts](#running-the-scripts)
5. [Troubleshooting](#troubleshooting)
6. [Next Steps](#next-steps)

---

## Prerequisites

### 1. Check Python Installation

Open **Command Prompt** (cmd) or **PowerShell** and run:

```cmd
python --version
```

You should see Python 3.8 or higher (e.g., `Python 3.11.5`).

**If Python is not installed:**

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Choose "Install Now"
5. Restart Command Prompt and verify: `python --version`

### 2. Check pip Installation

```cmd
pip --version
```

You should see pip version info. If not, Python installation may have failed.

### 3. Get an OpenAI API Key (for AI features)

1. Go to [platform.openai.com](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. **Save it securely** - you'll need it later

**Note:** The AI assistant requires GPT-4 access. Check your OpenAI account tier.

---

## Installation

### Step 1: Download the Repository

**Option A: Using Git**

If you have Git installed:

```cmd
cd C:\Users\YourUsername\Documents
git clone https://github.com/yourusername/Data-Analyst.git
cd Data-Analyst
```

**Option B: Download ZIP**

1. Download the repository as a ZIP file
2. Extract to a folder (e.g., `C:\Users\YourUsername\Documents\Data-Analyst`)
3. Open Command Prompt and navigate to the folder:
   ```cmd
   cd C:\Users\YourUsername\Documents\Data-Analyst
   ```

### Step 2: Create a Virtual Environment (Recommended)

Creating a virtual environment keeps dependencies isolated:

```cmd
python -m venv venv
```

**Activate the virtual environment:**

```cmd
venv\Scripts\activate
```

You should see `(venv)` at the start of your command prompt.

**To deactivate later:**
```cmd
deactivate
```

### Step 3: Install Dependencies

With the virtual environment activated:

```cmd
pip install -r requirements.txt
```

This will install:
- pandas (data manipulation)
- numpy (numerical computing)
- openai (OpenAI API client)
- gradio (web interface)
- python-dotenv (environment variables)

**Verify installation:**
```cmd
pip list
```

You should see all the packages listed.

---

## Configuration

### Step 1: Set Up OpenAI API Key

**Option A: Using .env file (Recommended)**

1. Copy the example file:
   ```cmd
   copy .env.example .env
   ```

2. Open `.env` in Notepad:
   ```cmd
   notepad .env
   ```

3. Replace `your_openai_api_key_here` with your actual API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

4. Save and close Notepad

**Option B: Set as Environment Variable**

```cmd
set OPENAI_API_KEY=sk-your-actual-key-here
```

**Note:** This only works for the current Command Prompt session.

**Option C: Set Permanently (System-wide)**

1. Press `Windows Key + X` → Select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `OPENAI_API_KEY`
6. Variable value: `sk-your-actual-key-here`
7. Click OK on all dialogs
8. Restart Command Prompt

---

## Running the Scripts

### Step 1: Create the Database Schema

```cmd
python create_ipeds_db_schema.py
```

**Expected output:**
```
Database schema created or verified in 'ipeds_data.db'.
```

**What this does:** Creates a new SQLite database file (`ipeds_data.db`) with empty tables.

---

### Step 2: Generate Synthetic Data

```cmd
python SyntheticDataforSchema2.py
```

**Expected output:**
```
Done! Total unique students: 2000
Enrollments inserted: 8541
Course enrollments inserted: 29847
Completions inserted: 643
```

**What this does:** Populates the database with realistic synthetic student data spanning 8 years.

**This will take:** ~10-30 seconds depending on your computer.

---

### Step 3: Launch the AI Assistant (Optional)

**Make sure your API key is configured first!**

```cmd
python ai_sql_python_assistant.py
```

**Expected output:**
```
Starting IPEDS AI Assistant...
Using database: ipeds_data.db
OpenAI Model: gpt-4o

Launching Gradio interface...
Running on local URL:  http://127.0.0.1:7860
```

**What this does:**
- Starts a web server on your computer
- Opens a web interface for asking questions about your data

**To use it:**
1. Open your web browser
2. Go to http://localhost:7860
3. Type questions like:
   - "What are the retention rates by race and ethnicity?"
   - "Show me average GPA by class year"
   - "How many students graduated in each program?"

**To stop the server:**
- Press `Ctrl+C` in the Command Prompt window

---

### Step 4: Generate CSV Data (Optional Alternative)

If you prefer CSV files instead of a database:

```cmd
python generate_synthetic_data.py
```

**Expected output:**
```
Student-level synthetic data generated in synthetic_student_level_data.csv.
```

**What this does:** Creates a CSV file with 200 student completion records.

---

### Step 5: Validate CSV Data (Optional)

To check your CSV data quality:

```cmd
python validate_data.py
```

**Expected output:** List of validation checks and warnings (if any).

---

### Step 6: Anonymize Data (Optional)

To anonymize student IDs in a CSV file:

```cmd
python anonymize_data.py synthetic_student_level_data.csv anonymized.csv translation.csv
```

**Expected output:**
```
Anonymized data written to: anonymized.csv
Translation table written to: translation.csv
```

**What this does:**
- Creates `anonymized.csv` with randomized student IDs
- Creates `translation.csv` with the mapping (keep secure!)

---

## Troubleshooting

### "Python is not recognized as an internal or external command"

**Solution:** Python is not in your PATH.

1. Find where Python is installed (usually `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3XX`)
2. Add it to PATH:
   - Windows Key + X → System → Advanced system settings
   - Environment Variables → System variables → Path → Edit
   - Click "New" and add the Python path
   - Also add the Scripts subfolder
3. Restart Command Prompt

**Or:** Reinstall Python and check "Add Python to PATH"

---

### "No module named 'pandas'" (or other packages)

**Solution:** Dependencies not installed.

```cmd
pip install -r requirements.txt
```

Make sure your virtual environment is activated (you should see `(venv)` in the prompt).

---

### "OPENAI_API_KEY environment variable not set"

**Solution:** API key not configured.

**Quick fix (temporary):**
```cmd
set OPENAI_API_KEY=sk-your-key-here
python ai_sql_python_assistant.py
```

**Permanent fix:** Create a `.env` file (see Configuration section above).

---

### "Database file not found"

**Solution:** Run schema creation first:

```cmd
python create_ipeds_db_schema.py
python SyntheticDataforSchema2.py
```

---

### "Port 7860 already in use"

**Solution:** Another program is using that port.

1. Open `ai_sql_python_assistant.py` in Notepad:
   ```cmd
   notepad ai_sql_python_assistant.py
   ```

2. Find the line (near the bottom):
   ```python
   iface.launch(share=False, server_port=7860)
   ```

3. Change `7860` to another number (e.g., `7861`, `8080`)

4. Save and try again

---

### Gradio Interface Won't Open

**Solution:** Manually open in browser.

After running `python ai_sql_python_assistant.py`, look for:
```
Running on local URL:  http://127.0.0.1:7860
```

Copy that URL and paste it into your browser.

---

### "Permission denied" when creating database

**Solution:** Run Command Prompt as Administrator.

1. Press Windows Key
2. Type "cmd"
3. Right-click "Command Prompt"
4. Select "Run as administrator"
5. Navigate to your project folder and try again

---

### OpenAI API Errors

**"Authentication error"**
- Your API key is wrong or expired
- Get a new key from platform.openai.com

**"Rate limit exceeded"**
- You've used your API quota
- Wait or upgrade your OpenAI plan

**"Model not found"**
- You don't have access to GPT-4
- Edit `ai_sql_python_assistant.py` and change `model="gpt-4o"` to `model="gpt-3.5-turbo"`

---

## Next Steps

### Explore the Data

**Option 1: Using the AI Assistant**
- Run `python ai_sql_python_assistant.py`
- Ask questions in plain English

**Option 2: Using SQL Directly**

Install a SQLite browser:
- Download [DB Browser for SQLite](https://sqlitebrowser.org/dl/)
- Open `ipeds_data.db`
- Write SQL queries in the "Execute SQL" tab

**Option 3: Using Python**

Create a new file `my_analysis.py`:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("ipeds_data.db")

query = """
SELECT
    race_ethnicity,
    AVG(avg_gpa) as avg_gpa,
    AVG(retained_next_term) as retention_rate
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
GROUP BY race_ethnicity
"""

df = pd.read_sql_query(query, conn)
print(df)
conn.close()
```

Run it:
```cmd
python my_analysis.py
```

---

### Modify Data Generation Parameters

Edit `SyntheticDataforSchema2.py` to change:

```python
total_years=8                      # Number of Fall terms
new_freshmen_each_fall=250         # Cohort size
senior_grad_prob=0.70              # Graduation rate
race_penalty_for_retention=0.05    # Set to 0 for no disparity
```

Then regenerate data:
```cmd
python SyntheticDataforSchema2.py
```

---

### Export Data for Excel

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("ipeds_data.db")
df = pd.read_sql_query("SELECT * FROM students", conn)
df.to_excel("students.xlsx", index=False)
conn.close()
```

Requires: `pip install openpyxl`

---

## Quick Reference

### Start a New Analysis Session

```cmd
cd C:\Users\YourUsername\Documents\Data-Analyst
venv\Scripts\activate
python ai_sql_python_assistant.py
```

### Regenerate All Data

```cmd
del ipeds_data.db
python create_ipeds_db_schema.py
python SyntheticDataforSchema2.py
```

### Update Dependencies

```cmd
pip install --upgrade -r requirements.txt
```

---

## Additional Resources

- **Main README**: [README.md](../README.md)
- **Mac Setup**: [SETUP_MAC.md](SETUP_MAC.md)
- **OpenAI Docs**: https://platform.openai.com/docs
- **Pandas Docs**: https://pandas.pydata.org/docs
- **SQLite Tutorial**: https://www.sqlitetutorial.net

---

## Getting Help

If you encounter issues not covered here:

1. Check the main [README.md](../README.md) troubleshooting section
2. Verify all prerequisites are installed correctly
3. Try running scripts one at a time
4. Check error messages carefully - they often indicate the problem

---

**Happy analyzing!** 🎉
