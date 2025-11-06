# Quick Start Guide - IPEDS Data Analysis Toolkit

Get up and running in **under 5 minutes** with the automated installer!

---

## One-Command Installation

### Windows

1. **Download** this repository (or clone it)
2. **Open Command Prompt** in the project folder
3. **Run:**
   ```cmd
   setup.bat
   ```

That's it! The installer will:
- ✓ Check Python version
- ✓ Create virtual environment
- ✓ Install all dependencies
- ✓ Ask for your OpenAI API key
- ✓ Create the database
- ✓ Generate sample data

### Mac / Linux

1. **Download** this repository (or clone it)
2. **Open Terminal** in the project folder
3. **Run:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

The installer handles everything automatically!

---

## Launching the AI Assistant

After installation:

### Windows
```cmd
start.bat
```

### Mac / Linux
```bash
./start.sh
```

Then open your browser to: **http://localhost:7860**

---

## What You Need

### Required
- **Python 3.8+** ([Download here](https://www.python.org/downloads/))
  - ⚠️ On Windows: Check "Add Python to PATH" during installation

### Optional (for AI features)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
  - You can skip this during setup and add it later
  - Edit `.env` file and add: `OPENAI_API_KEY=sk-your-key-here`

---

## Installation Options

### Skip Sample Data Generation

If you want to install but not generate data immediately:

**Windows:**
```cmd
python install.py --skip-data
```

**Mac/Linux:**
```bash
python3 install.py --skip-data
```

Generate data later with:
```bash
python SyntheticDataforSchema2.py
```

### Provide API Key Directly

**Windows:**
```cmd
python install.py --api-key sk-your-key-here
```

**Mac/Linux:**
```bash
python3 install.py --api-key sk-your-key-here
```

---

## Troubleshooting

### "Python is not found"

**Windows:**
- Install Python from [python.org](https://www.python.org/downloads/)
- During installation, check ✓ "Add Python to PATH"
- Restart Command Prompt

**Mac:**
```bash
brew install python3
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### "Permission denied" (Mac/Linux)

Make the scripts executable:
```bash
chmod +x setup.sh start.sh install.py
```

### Installation Fails

1. Check Python version: `python --version` (or `python3 --version`)
   - Must be 3.8 or higher
2. Make sure you have internet connection (to download packages)
3. Try running with administrator/sudo if you get permission errors

### "OpenAI API key not set"

You can:
1. **Edit `.env` file** and add your key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
2. **Or set environment variable:**
   - Windows: `set OPENAI_API_KEY=sk-your-key`
   - Mac/Linux: `export OPENAI_API_KEY=sk-your-key`

---

## What Gets Installed?

### Directory Structure After Installation

```
Data-Analyst/
├── venv/                    # Virtual environment (created)
├── ipeds_data.db            # SQLite database (created)
├── .env                     # Your API key (created)
│
├── install.py               # Main installer
├── setup.bat / setup.sh     # Quick installers
├── start.bat / start.sh     # Quick launch scripts
│
├── requirements.txt         # Python dependencies
├── README.md               # Full documentation
├── QUICKSTART.md           # This file
└── [Python scripts...]     # Analysis tools
```

### Installed Python Packages

- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `openai` - OpenAI API client
- `gradio` - Web interface
- `python-dotenv` - Environment variables

---

## Next Steps After Installation

### 1. Launch the AI Assistant

**Windows:** Run `start.bat`
**Mac/Linux:** Run `./start.sh`

Open browser to http://localhost:7860

### 2. Ask Questions

Try these example questions:
- "What are the retention rates by race and ethnicity?"
- "Show me average GPA by class year"
- "How many students graduated in each program?"
- "What's the distribution of students across different terms?"

### 3. Explore the Data

**Using SQL:**
```bash
sqlite3 ipeds_data.db
```

**Using Python:**
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("ipeds_data.db")
df = pd.read_sql_query("SELECT * FROM students LIMIT 10", conn)
print(df)
```

### 4. Generate CSV Data (Optional)

```bash
python generate_synthetic_data.py
```

Creates `synthetic_student_level_data.csv` with completion records.

### 5. Validate Data

```bash
python validate_data.py
```

Runs quality checks on CSV data.

### 6. Anonymize Data

```bash
python anonymize_data.py input.csv output.csv translation.csv
```

---

## Manual Installation (If Automated Fails)

If the automated installer doesn't work, follow the manual steps:

### Windows
See [SETUP_WINDOWS.md](SETUP_WINDOWS.md)

### Mac/Linux
See [SETUP_MAC.md](SETUP_MAC.md)

---

## Getting Help

### Check Documentation
- **README.md** - Complete documentation
- **SETUP_WINDOWS.md** - Detailed Windows setup
- **SETUP_MAC.md** - Detailed Mac/Linux setup

### Common Issues
1. Make sure Python 3.8+ is installed
2. Check that you have internet connection
3. Ensure you have write permissions in the directory
4. On Mac/Linux, make scripts executable: `chmod +x setup.sh start.sh`

### Still Having Issues?

1. Try the manual installation guides
2. Check error messages carefully - they usually indicate the problem
3. Make sure all prerequisites are met

---

## Uninstallation

To remove everything:

1. Delete the project folder
2. That's it! Everything is self-contained.

The installer doesn't modify system settings or install global packages.

---

## Summary

**Quickest path to running:**

1. Download repository
2. Run `setup.bat` (Windows) or `./setup.sh` (Mac/Linux)
3. Enter OpenAI API key when prompted
4. Run `start.bat` or `./start.sh`
5. Open http://localhost:7860
6. Start analyzing!

**Total time:** ~3-5 minutes (depending on internet speed)

---

**Ready to dive deeper?** Check out [README.md](README.md) for complete documentation!
