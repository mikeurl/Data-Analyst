# IPEDS Data Analysis Toolkit

An AI-powered tool for analyzing student enrollment and completion data. Ask questions in plain English and get instant answers with charts and insights.

---

## What Does This Do?

This toolkit lets you:
- ✅ Analyze student retention rates
- ✅ Track GPA trends by demographics
- ✅ Explore graduation patterns
- ✅ Ask questions in plain English (powered by AI)
- ✅ Generate reports automatically

All with synthetic IPEDS-style data included.

---

## Installation

Choose your operating system:

### 🪟 Windows
**[Follow the Windows Setup Guide →](docs/SETUP_WINDOWS.md)**

### 🍎 Mac
**[Follow the Mac Setup Guide →](docs/SETUP_MAC.md)**

Each guide is written for complete beginners. No command line experience needed!

**Time to install:** 10 minutes
**Time to get first result:** 2 minutes after installation

---

## Quick Summary

Once installed, you'll be able to:

1. **Start the tool** - Double-click `start.bat` (Windows) or run `./start.sh` (Mac)
2. **Ask questions** - Type questions like "What's the retention rate for freshmen?"
3. **Get instant answers** - See SQL code, results, and explanations

---

## Example Questions You Can Ask

- "How many students are in each program?"
- "What are the retention rates by race and ethnicity?"
- "Show me average GPA by class year"
- "Which programs have the highest graduation rates?"
- "How many students dropped out vs graduated?"

---

## What's Included

### Core Analysis Scripts
- `create_ipeds_db_schema.py` - Creates the database structure
- `SyntheticDataforSchema2.py` - Generates realistic student data
- `ai_sql_python_assistant.py` - AI-powered query interface
- `validate_data.py` - Data quality checks
- `anonymize_data.py` - Privacy tools

### Easy Installation
- `setup.bat` / `setup.sh` - One-click installers
- `start.bat` / `start.sh` - One-click launchers
- Automatic database creation
- Sample data generation

### Documentation
- **[Windows Setup](docs/SETUP_WINDOWS.md)** - Step-by-step for Windows
- **[Mac Setup](docs/SETUP_MAC.md)** - Step-by-step for Mac

---

## Requirements

- **Python 3.8+** (installation guide included in setup docs)
- **10 minutes** for installation
- **Internet connection** to download packages
- **OpenAI API key** (optional, for AI features - can be added later)

---

## Features

### 🤖 AI-Powered Analysis
Ask questions in plain English. The AI generates SQL queries, runs them, and explains the results.

### 📊 Realistic Data
Pre-loaded with 2,000+ synthetic students across 8 years, including:
- Enrollment records
- Course grades
- Retention tracking
- Graduation data
- Demographics

### 🔒 Privacy Built-In
- All data is synthetic (no real students)
- Anonymization tools included
- Works completely offline (except for AI features)

### 📈 Ready for Analysis
- SQLite database format
- CSV export options
- Compatible with Excel, R, Python, Tableau

---

## Getting Help

### Installation Issues
Check the setup guides:
- [Windows troubleshooting](docs/SETUP_WINDOWS.md#troubleshooting)
- [Mac troubleshooting](docs/SETUP_MAC.md#troubleshooting)

### Common Problems

**"Python not found"**
- Follow Step 1 in the setup guide for your OS

**"Web page won't open"**
- Make sure you see "Running on local URL: http://127.0.0.1:7860"
- Open your browser and go to http://localhost:7860

**"AI queries don't work"**
- You need an OpenAI API key (get one at https://platform.openai.com)
- Add it to the `.env` file (instructions in setup guides)

---

## Technical Details

### Database Schema
- **students** - Demographics and IDs
- **enrollments** - Term-by-term enrollment with retention flags
- **courses** - Course catalog
- **course_enrollments** - Individual course grades
- **completions** - Degrees and certificates awarded

### Data Model
Follows IPEDS (Integrated Postsecondary Education Data System) standards for higher education reporting.

---

## License

This is an educational and research tool. All generated data is synthetic and does not represent real individuals.

---

## Quick Start (Summary)

1. **Install Python** (see setup guide for your OS)
2. **Download this repository** (green "Code" button → "Download ZIP")
3. **Run the installer** (`setup.bat` on Windows, `./setup.sh` on Mac)
4. **Start the tool** (`start.bat` on Windows, `./start.sh` on Mac)
5. **Open your browser** to http://localhost:7860
6. **Start analyzing!** 🎉

---

**Ready to get started?**
- **[Windows Users: Start Here →](docs/SETUP_WINDOWS.md)**
- **[Mac Users: Start Here →](docs/SETUP_MAC.md)**
