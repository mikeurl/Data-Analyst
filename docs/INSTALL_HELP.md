# Installation Help - What to Expect

## The Problem

When you run `./setup.sh`, it looks like nothing is happening. **This is normal!** The installer is working, but it takes **5-10 minutes** to download and install everything.

## What's Actually Happening

Here's what the installer does and how long each step takes:

### Step 1: Check Python (5 seconds)
```
Python found. Starting installation...
✓ Python 3.11.14 is compatible
```

### Step 2: Create Virtual Environment (30-60 seconds)
```
Creating Virtual Environment
ℹ Creating virtual environment (this may take a minute)...
✓ Virtual environment created successfully
```
**This creates a folder called `venv/`**

### Step 3: Install Dependencies (3-5 minutes) ⏰ **THIS IS THE SLOW PART**
```
Installing Dependencies
ℹ Installing packages (this may take a few minutes)...
Downloading pandas...
Downloading numpy...
Downloading openai...
Downloading gradio...
[Many more lines of downloading/installing]
✓ All dependencies installed successfully
```
**Don't cancel! This is downloading ~100MB of Python packages from the internet.**

### Step 4: API Key (waits for you)
```
Configuring OpenAI API Key

ℹ You need an OpenAI API key to use the AI assistant features.
ℹ Get one at: https://platform.openai.com/api-keys

Enter your OpenAI API key (or press Enter to skip): _
```
**Just press Enter if you don't have one yet**

### Step 5: Create Database (5 seconds)
```
Creating Database Schema
✓ Database schema created successfully
```

### Step 6: Generate Data (30 seconds)
```
Generating Sample Data
ℹ Generating data...
Done! Total unique students: 2000
✓ Sample data generated successfully
```

### Step 7: Done!
```
Installation Complete!

To launch the AI Assistant, run: ./start.sh
```

---

## Three Ways to Install

### Option 1: Full Install (Recommended, but slow)
**Takes 5-10 minutes**
```bash
./setup.sh
```
Then wait... and wait... it's downloading packages from the internet.

### Option 2: Quick Demo (Faster)
**Takes 2-3 minutes** (skips sample data)
```bash
python3 quick_demo.py
```
You can generate data later with: `python SyntheticDataforSchema2.py`

### Option 3: Manual (Step by Step)
If the installer seems stuck, you can do it manually:

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Install packages (THIS IS SLOW - 3-5 minutes)
pip install -r requirements.txt

# 4. Create database
python create_ipeds_db_schema.py

# 5. Generate data
python SyntheticDataforSchema2.py

# 6. Run the AI assistant
python ai_sql_python_assistant.py
```

---

## How to Know It's Working

### Look for these signs:
1. A `venv/` folder appears (after step 2)
2. You see "Downloading..." messages (during step 3)
3. The terminal shows package names like "pandas", "numpy", "openai"
4. It asks for your API key (step 4)
5. An `ipeds_data.db` file appears (after step 5)

### Check if venv was created:
```bash
ls -la venv/
```
You should see folders: `bin/`, `lib/`, `include/`

### Check if packages are installed:
```bash
source venv/bin/activate
pip list
```
You should see: pandas, numpy, openai, gradio

---

## Troubleshooting

### "It's been 30 seconds and nothing happened!"
**→ Wait longer.** The first download takes 3-5 minutes.

### "I pressed Ctrl+C by accident"
**→ Just run `./setup.sh` again.** It will reuse what it already created.

### "I don't have an OpenAI API key"
**→ Press Enter to skip.** You can add it later to the `.env` file.

### "It says 'command not found: ./setup.sh'"
**→ Run this first:**
```bash
chmod +x setup.sh
```

### "Still not working!"
**→ Try the manual installation** (see Option 3 above)

---

## Quick Test

Want to verify everything is working? Run:

```bash
./test_install.sh
```

This checks all the components without actually installing anything.

---

## TL;DR

**The installer DOES work, it just takes 5-10 minutes because it's downloading packages from the internet. Be patient!**

If you don't want to wait, use the quick demo:
```bash
python3 quick_demo.py
```
