# IPEDS Data Analysis Toolkit

A comprehensive Python toolkit for generating, validating, anonymizing, and analyzing IPEDS (Integrated Postsecondary Education Data System) student completion data with AI-powered natural language query capabilities.

## Overview

This toolkit provides a complete workflow for working with IPEDS-like student data:

1. **Database Schema Creation** - SQLite database with proper relational structure
2. **Synthetic Data Generation** - Realistic student enrollment and completion data
3. **Data Validation** - Comprehensive checks for data quality
4. **Data Anonymization** - Privacy-preserving student ID randomization
5. **AI-Powered Analysis** - Natural language queries using OpenAI GPT models

## Features

- **Realistic Data Modeling**: Multi-year student populations with GPA-based retention, class progression, and graduations
- **Two Data Formats**: SQLite database (relational) and CSV (flat files)
- **AI Assistant**: Ask questions in plain English and get SQL + Python analysis automatically
- **Data Privacy Tools**: Built-in anonymization with translation tables
- **Validation Suite**: Automated checks for IPEDS compliance and data quality

## Quick Start

> **🚀 NEW: Automated Installer!** Get up and running in under 5 minutes with one command:
> - **Windows**: Run `setup.bat`
> - **Mac/Linux**: Run `./setup.sh`
>
> See [QUICKSTART.md](docs/QUICKSTART.md) for instant setup instructions!

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for AI assistant features - optional, can add later)

### Automated Installation (Recommended)

**Windows:**
```cmd
setup.bat
```

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

The installer will:
- ✓ Check Python version
- ✓ Create virtual environment
- ✓ Install dependencies
- ✓ Configure API key
- ✓ Create database
- ✓ Generate sample data

Then launch with `start.bat` (Windows) or `./start.sh` (Mac/Linux)!

### Manual Installation

If you prefer manual setup or the automated installer fails:
- **Windows**: See [SETUP_WINDOWS.md](docs/SETUP_WINDOWS.md)
- **Mac/Linux**: See [SETUP_MAC.md](docs/SETUP_MAC.md)

### Basic Usage (Manual)

1. **Create the database schema:**
   ```bash
   python create_ipeds_db_schema.py
   ```

2. **Generate synthetic data:**
   ```bash
   python SyntheticDataforSchema2.py
   ```

3. **Launch the AI assistant (optional):**
   ```bash
   python ai_sql_python_assistant.py
   ```
   Then open your browser to http://localhost:7860

## Project Structure

```
Data-Analyst/
│
├── install.py                     # 🆕 Automated installer (cross-platform)
├── setup.bat                      # 🆕 Windows quick installer
├── setup.sh                       # 🆕 Mac/Linux quick installer
├── start.bat                      # 🆕 Windows quick launcher
├── start.sh                       # 🆕 Mac/Linux quick launcher
│
├── create_ipeds_db_schema.py      # Creates SQLite database schema
├── SyntheticDataforSchema2.py     # Generates synthetic student data (DB)
├── generate_synthetic_data.py     # Generates synthetic student data (CSV)
├── validate_data.py               # Validates CSV data files
├── anonymize_data.py              # Anonymizes student IDs in CSV files
├── ai_sql_python_assistant.py     # AI-powered query interface
│
├── requirements.txt               # Python dependencies
├── .env.example                   # Example environment variables
├── .gitignore                     # Git ignore rules
│
├── docs/                          # 📁 Documentation
│   ├── QUICKSTART.md             # Quick installation guide
│   ├── START_HERE.md             # Troubleshooting guide
│   ├── INSTALL_HELP.md           # Installation help
│   ├── WHAT_GETS_CREATED.md      # File creation guide
│   ├── HOW_TO_MERGE.md           # Merging guide
│   ├── SETUP_WINDOWS.md          # Windows setup instructions
│   └── SETUP_MAC.md              # Mac/Linux setup instructions
│
└── README.md                      # This file
```

## Core Scripts

### 1. create_ipeds_db_schema.py

Creates a SQLite database with five related tables:
- `students` - Demographics (race/ethnicity, gender, DOB)
- `enrollments` - Term enrollments with retention tracking
- `courses` - Course catalog
- `course_enrollments` - Individual grades
- `completions` - Degrees/certificates awarded

**Usage:**
```bash
python create_ipeds_db_schema.py
```

**Output:** Creates `ipeds_data.db`

---

### 2. SyntheticDataforSchema2.py

Generates realistic multi-year student population data with:
- ~250 new freshmen per Fall term (with variation)
- GPA-based retention modeling
- Class progression (Freshman → Senior)
- Graduations and dropouts
- Course enrollments with letter grades

**Usage:**
```bash
python SyntheticDataforSchema2.py
```

**Configuration:** Edit parameters in the script:
- `total_years`: Number of Fall terms (default: 8)
- `new_freshmen_each_fall`: Base cohort size (default: 250)
- `senior_grad_prob`: Graduation probability (default: 0.70)
- `race_penalty_for_retention`: Disparity modeling (default: 0.05)

**Output:** Populates `ipeds_data.db` with thousands of student records

**Note on Retention Modeling:** The script includes a `race_penalty_for_retention` parameter that simulates observed disparities in retention rates. This is for research/analysis purposes to model real-world patterns. Set to `0` if you want equal retention rates across all demographics.

---

### 3. generate_synthetic_data.py

Generates CSV-format completion data (alternative to database approach).

**Usage:**
```bash
python generate_synthetic_data.py
```

**Output:** Creates `synthetic_student_level_data.csv`

**Use Cases:**
- Testing validation scripts
- Creating sample datasets for reporting
- Demonstrating anonymization workflows

---

### 4. validate_data.py

Validates CSV data files for IPEDS compliance.

**Checks performed:**
- Required columns present
- CIP code format (XX.XXXX)
- Award category/subtype consistency
- Age ranges (0-100)
- Gender values
- Data distribution analysis

**Usage:**
```bash
python validate_data.py
```

**To use with custom files:**
```python
from validate_data import validate_student_data

issues = validate_student_data("your_file.csv")
for issue in issues:
    print(issue)
```

---

### 5. anonymize_data.py

Anonymizes student IDs in CSV files for privacy protection.

**Usage:**
```bash
python anonymize_data.py input.csv output_anonymized.csv translation_table.csv
```

**Outputs:**
1. `output_anonymized.csv` - Data with randomized student IDs
2. `translation_table.csv` - Mapping for re-identification (keep secure!)

**Example:**
```bash
python anonymize_data.py synthetic_student_level_data.csv \
    anonymized_data.csv \
    translation_table.csv
```

**Security Note:** The translation table allows re-identification. Store it securely and separately from anonymized data.

---

### 6. ai_sql_python_assistant.py

AI-powered interface for querying IPEDS data using natural language.

**Features:**
- Ask questions in plain English
- Automatic SQL query generation
- Python-based data analysis
- Natural language explanations
- Web-based Gradio interface

**Requirements:**
- OpenAI API key (GPT-4 access recommended)
- Generated database (`ipeds_data.db`)

**Usage:**
```bash
python ai_sql_python_assistant.py
```

Then open http://localhost:7860 in your browser.

**Example queries:**
- "What are the retention rates by race and ethnicity?"
- "Show me the average GPA by class year"
- "How many students graduated in each program?"
- "What's the distribution of students across different terms?"

**Security Warning:** This script uses `exec()` for code execution. Use only in trusted environments with controlled inputs. Not recommended for production without additional security measures.

---

## Data Model

### Database Schema

The SQLite database follows an IPEDS-like relational structure:

```
students (student_id, first_name, last_name, dob, gender, race_ethnicity)
    │
    ├─→ enrollments (enrollment_id, student_id, term, program, status,
    │                 retained_next_term, class_year, avg_gpa)
    │       │
    │       └─→ course_enrollments (course_enrollment_id, enrollment_id,
    │                                course_id, grade, grade_points)
    │               │
    │               └─→ courses (course_id, course_code, course_name, credit_hours)
    │
    └─→ completions (completion_id, student_id, award_type, cip_code, completion_date)
```

### Key Fields

- **CIP Codes**: Classification of Instructional Programs (e.g., "11.0101" = Computer Science)
- **Class Year**: 1=Freshman, 2=Sophomore, 3=Junior, 4=Senior
- **Retained Next Term**: 0=Did not return, 1=Returned
- **Grade Points**: 4.0=A, 3.0=B, 2.0=C, 1.0=D, 0.0=F

---

## Common Workflows

### Workflow 1: Database Analysis

1. Create schema: `python create_ipeds_db_schema.py`
2. Generate data: `python SyntheticDataforSchema2.py`
3. Analyze with AI: `python ai_sql_python_assistant.py`

### Workflow 2: CSV Analysis

1. Generate CSV: `python generate_synthetic_data.py`
2. Validate: `python validate_data.py`
3. Anonymize: `python anonymize_data.py input.csv output.csv translation.csv`

### Workflow 3: Custom Analysis

```python
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect("ipeds_data.db")

# Run custom queries
query = """
SELECT
    race_ethnicity,
    AVG(avg_gpa) as average_gpa,
    AVG(retained_next_term) as retention_rate
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
GROUP BY race_ethnicity
"""

df = pd.read_sql_query(query, conn)
print(df)
```

---

## Configuration

### Environment Variables

The AI assistant requires an OpenAI API key:

1. Copy `.env.example` to `.env`
2. Edit `.env` and add your key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

**Or** set it in your shell:
- **Windows**: `set OPENAI_API_KEY=sk-your-key`
- **Mac/Linux**: `export OPENAI_API_KEY=sk-your-key`

### Script Parameters

Most scripts have configurable parameters at the top of the file. Common ones:

**SyntheticDataforSchema2.py:**
```python
total_years=8                    # Number of Fall terms
new_freshmen_each_fall=250       # Base cohort size
senior_grad_prob=0.70           # Graduation probability
race_penalty_for_retention=0.05  # Disparity modeling (0 = no disparity)
```

**generate_synthetic_data.py:**
```python
num_students=200  # Number of completion records
seed=42          # Random seed for reproducibility
```

---

## Troubleshooting

### "Database file not found"
Run `python create_ipeds_db_schema.py` first.

### "OpenAI API key not set"
Set the `OPENAI_API_KEY` environment variable or create a `.env` file.

### "No module named 'openai'" (or other packages)
Install dependencies: `pip install -r requirements.txt`

### "Port 7860 already in use"
Edit `ai_sql_python_assistant.py` and change `server_port=7860` to another port.

### Validation fails with CIP code errors
Ensure CIP codes follow the format "XX.XXXX" (e.g., "11.0101").

---

## Important Notes

### Security Considerations

1. **API Keys**: Never commit your `.env` file to git. Use `.env.example` as a template.
2. **exec() Usage**: The AI assistant uses `exec()` for code execution. Only use in trusted environments.
3. **Translation Tables**: Store anonymization translation tables securely and separately from anonymized data.

### Data Privacy

- All generated data is **synthetic** - no real student information is used
- The anonymization tool helps protect privacy in real data scenarios
- Follow your institution's data governance policies

### Research Ethics

The retention modeling includes parameters that can simulate demographic disparities. This is intended for:
- Understanding existing equity gaps
- Testing intervention strategies
- Research and educational purposes

**It is not intended to perpetuate bias.** Consider carefully whether including disparities serves your analysis goals. Set `race_penalty_for_retention=0` for equal retention rates.

---

## Dependencies

See [requirements.txt](requirements.txt) for full list:

- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `openai` - OpenAI API client
- `gradio` - Web interface
- `python-dotenv` - Environment variable management (optional)
- `sqlite3` - Database (included in Python standard library)

---

## Contributing

This is a toolkit for educational and research purposes. To improve it:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## License

This project is provided as-is for educational and research purposes.

---

## Support

For issues, questions, or suggestions:
1. Check the troubleshooting section above
2. Review the setup guides (docs/SETUP_WINDOWS.md, docs/SETUP_MAC.md)
3. Open an issue on the repository

---

## Acknowledgments

- IPEDS data standards from the National Center for Education Statistics (NCES)
- OpenAI GPT models for natural language processing
- Gradio framework for web interfaces

---

## Version History

- **v1.0** - Initial release with core functionality
  - Database schema creation
  - Synthetic data generation
  - AI-powered query interface
  - Validation and anonymization tools
