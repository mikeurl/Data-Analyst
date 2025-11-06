# IPEDS Data Analysis Toolkit - Mac/Linux Setup Guide

Complete step-by-step instructions for setting up and running the IPEDS Data Analysis Toolkit on macOS and Linux.

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

Open **Terminal** and run:

```bash
python3 --version
```

You should see Python 3.8 or higher (e.g., `Python 3.11.5`).

**If Python is not installed:**

**macOS:**
```bash
# Install Homebrew first (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install python3 python3-pip
```

### 2. Check pip Installation

```bash
pip3 --version
```

You should see pip version info.

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

```bash
cd ~/Documents
git clone https://github.com/yourusername/Data-Analyst.git
cd Data-Analyst
```

**Option B: Download ZIP**

1. Download the repository as a ZIP file
2. Extract to a folder (e.g., `~/Documents/Data-Analyst`)
3. Open Terminal and navigate:
   ```bash
   cd ~/Documents/Data-Analyst
   ```

### Step 2: Create a Virtual Environment (Recommended)

Creating a virtual environment keeps dependencies isolated:

```bash
python3 -m venv venv
```

**Activate the virtual environment:**

```bash
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

**To deactivate later:**
```bash
deactivate
```

### Step 3: Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This will install:
- pandas (data manipulation)
- numpy (numerical computing)
- openai (OpenAI API client)
- gradio (web interface)
- python-dotenv (environment variables)

**Verify installation:**
```bash
pip list
```

You should see all the packages listed.

---

## Configuration

### Step 1: Set Up OpenAI API Key

**Option A: Using .env file (Recommended)**

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your preferred editor:
   ```bash
   nano .env
   # or
   vim .env
   # or
   open -e .env  # macOS only - opens in TextEdit
   ```

3. Replace `your_openai_api_key_here` with your actual API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

4. Save and close the editor
   - nano: `Ctrl+X`, then `Y`, then `Enter`
   - vim: Press `Esc`, type `:wq`, press `Enter`

**Option B: Set as Environment Variable (Temporary)**

```bash
export OPENAI_API_KEY=sk-your-actual-key-here
```

**Note:** This only works for the current Terminal session.

**Option C: Set Permanently in Shell Profile**

Add to your shell configuration file:

**For bash (add to `~/.bashrc` or `~/.bash_profile`):**
```bash
echo 'export OPENAI_API_KEY=sk-your-actual-key-here' >> ~/.bashrc
source ~/.bashrc
```

**For zsh (macOS default, add to `~/.zshrc`):**
```bash
echo 'export OPENAI_API_KEY=sk-your-actual-key-here' >> ~/.zshrc
source ~/.zshrc
```

---

## Running the Scripts

### Step 1: Create the Database Schema

```bash
python create_ipeds_db_schema.py
```

**Expected output:**
```
Database schema created or verified in 'ipeds_data.db'.
```

**What this does:** Creates a new SQLite database file (`ipeds_data.db`) with empty tables.

---

### Step 2: Generate Synthetic Data

```bash
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

```bash
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
- Press `Ctrl+C` in the Terminal window

---

### Step 4: Generate CSV Data (Optional Alternative)

If you prefer CSV files instead of a database:

```bash
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

```bash
python validate_data.py
```

**Expected output:** List of validation checks and warnings (if any).

---

### Step 6: Anonymize Data (Optional)

To anonymize student IDs in a CSV file:

```bash
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

### "command not found: python"

**Solution:** Use `python3` instead of `python`:

```bash
python3 create_ipeds_db_schema.py
```

**Or create an alias:**
```bash
alias python=python3
```

Add to `~/.bashrc` or `~/.zshrc` to make permanent.

---

### "No module named 'pandas'" (or other packages)

**Solution:** Dependencies not installed or virtual environment not activated.

1. Make sure virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

### "OPENAI_API_KEY environment variable not set"

**Solution:** API key not configured.

**Quick fix (temporary):**
```bash
export OPENAI_API_KEY=sk-your-key-here
python ai_sql_python_assistant.py
```

**Permanent fix:** Create a `.env` file (see Configuration section above).

---

### "Database file not found"

**Solution:** Run schema creation first:

```bash
python create_ipeds_db_schema.py
python SyntheticDataforSchema2.py
```

---

### "Port 7860 already in use"

**Solution:** Another program is using that port.

**Option 1: Find and kill the process**
```bash
# Find what's using the port
lsof -i :7860

# Kill it (replace PID with actual process ID)
kill -9 PID
```

**Option 2: Use a different port**

1. Open `ai_sql_python_assistant.py`:
   ```bash
   nano ai_sql_python_assistant.py
   ```

2. Find the line (near the bottom):
   ```python
   iface.launch(share=False, server_port=7860)
   ```

3. Change `7860` to another number (e.g., `7861`, `8080`)

4. Save and try again

---

### Gradio Interface Won't Open Automatically

**Solution:** Manually open in browser.

After running `python ai_sql_python_assistant.py`, look for:
```
Running on local URL:  http://127.0.0.1:7860
```

Copy that URL and paste it into your browser.

---

### "Permission denied" when creating database

**Solution:** Check file/directory permissions.

```bash
# Make sure you have write permissions
ls -la

# If needed, fix permissions
chmod 755 .
```

---

### macOS: "Python quit unexpectedly"

**Solution:** Install Python properly through Homebrew, not the system Python.

```bash
brew install python3
```

Then create a new virtual environment with the Homebrew Python.

---

### Linux: "Unable to locate package python3-pip"

**Solution:** Update package lists first.

```bash
sudo apt update
sudo apt install python3-pip
```

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

**macOS:**
- Install [DB Browser for SQLite](https://sqlitebrowser.org/dl/)
- Open `ipeds_data.db`

**Linux:**
```bash
sudo apt install sqlitebrowser  # Ubuntu/Debian
# or
sudo dnf install sqlitebrowser  # Fedora
```

**Command-line SQLite:**
```bash
sqlite3 ipeds_data.db
.tables
SELECT * FROM students LIMIT 5;
.quit
```

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
```bash
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
```bash
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

### Create Shell Aliases for Common Tasks

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# IPEDS shortcuts
alias ipeds-activate='cd ~/Documents/Data-Analyst && source venv/bin/activate'
alias ipeds-reset='rm ipeds_data.db && python create_ipeds_db_schema.py && python SyntheticDataforSchema2.py'
alias ipeds-ai='python ai_sql_python_assistant.py'
```

Then use:
```bash
ipeds-activate  # Navigate to project and activate environment
ipeds-reset     # Regenerate all data
ipeds-ai        # Launch AI assistant
```

---

## Quick Reference

### Start a New Analysis Session

```bash
cd ~/Documents/Data-Analyst
source venv/bin/activate
python ai_sql_python_assistant.py
```

### Regenerate All Data

```bash
rm ipeds_data.db
python create_ipeds_db_schema.py
python SyntheticDataforSchema2.py
```

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Check Database Size

```bash
ls -lh ipeds_data.db
```

### Quick SQL Query

```bash
sqlite3 ipeds_data.db "SELECT COUNT(*) FROM students;"
```

---

## Additional Resources

- **Main README**: [README.md](README.md)
- **Windows Setup**: [SETUP_WINDOWS.md](SETUP_WINDOWS.md)
- **OpenAI Docs**: https://platform.openai.com/docs
- **Pandas Docs**: https://pandas.pydata.org/docs
- **SQLite Tutorial**: https://www.sqlitetutorial.net

---

## Getting Help

If you encounter issues not covered here:

1. Check the main [README.md](README.md) troubleshooting section
2. Verify all prerequisites are installed correctly
3. Make sure virtual environment is activated (`source venv/bin/activate`)
4. Try running scripts one at a time
5. Check error messages carefully - they often indicate the problem

---

**Happy analyzing!** 🎉
