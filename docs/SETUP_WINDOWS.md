# Installing the IPEDS Data Analyst - Windows

A complete, step-by-step guide for beginners. No experience needed!

---

## What You Need

1. A Windows computer (Windows 10 or 11)
2. About 10 minutes
3. Internet connection

---

## Step 1: Install Python

Python is the programming language this tool uses.

### Check if Python is Already Installed

1. Click the **Start button** (Windows logo in bottom-left corner)
2. Type: `cmd`
3. Click on **Command Prompt** (it's a black icon)
4. A black window will open. Type: `python --version` and press **Enter**

**If you see something like "Python 3.11.5":**
- Great! Python is already installed. Skip to Step 2.

**If you see an error or "command not found":**
- Continue below to install Python.

### Install Python

1. Open your web browser (Edge, Chrome, etc.)
2. Go to: https://www.python.org/downloads/
3. Click the big yellow button that says **"Download Python"**
4. Wait for the download to finish (it's about 25 MB)
5. Open your **Downloads** folder
6. Double-click the file that starts with `python-` (like `python-3.11.5.exe`)
7. **IMPORTANT**: Check the box that says **"Add Python to PATH"** (at the bottom)
8. Click **"Install Now"**
9. Wait for installation to complete (takes 2-3 minutes)
10. Click **"Close"**

### Verify Python Installed

1. Click **Start** button
2. Type: `cmd`
3. Click **Command Prompt**
4. Type: `python --version` and press **Enter**
5. You should see: `Python 3.11.5` (or similar)

✅ Python is now installed!

---

## Step 2: Download the Data Analyst Tool

1. Open your web browser
2. Go to: https://github.com/mikeurl/Data-Analyst
3. Click the green **"Code"** button
4. Click **"Download ZIP"**
5. Wait for download to complete
6. Open your **Downloads** folder
7. Find the file `Data-Analyst-main.zip`
8. Right-click on it
9. Choose **"Extract All..."**
10. Click **"Extract"**
11. A new folder will open called `Data-Analyst-main`

✅ Files are downloaded!

---

## Step 3: Run the Installer

1. Open the `Data-Analyst-main` folder (if not already open)
2. Double-click on `setup.bat`
3. If Windows shows a security warning, click **"More info"** then **"Run anyway"**
4. A black window will open and start installing

### What You'll See

```
========================================================================
 IPEDS Data Analysis Toolkit - Windows Quick Installer
========================================================================

Python found. Starting installation...
```

Then you'll see:
```
Checking Python Version
✓ Python 3.11.5 is compatible

Creating Virtual Environment
ℹ Creating virtual environment (this may take a minute)...
✓ Virtual environment created successfully

Installing Dependencies
ℹ Installing packages (this will take 2-3 minutes)...
[You'll see lots of text scrolling by - this is normal!]
✓ All dependencies installed successfully

Configuring OpenAI API Key
Enter your OpenAI API key (or press Enter to skip):
```

### About the API Key

The API key lets you ask questions to the AI. You can:
- **Press Enter to skip** (you can add it later)
- **Or paste your key** if you have one from https://platform.openai.com/api-keys

After that, it will:
```
Creating Database Schema
✓ Database schema created successfully

Generating Sample Data
ℹ Generating data...
Done! Total unique students: 2000
✓ Sample data generated successfully

========================================================================
 Installation Complete!
========================================================================
```

✅ Installation is done!

**Leave the black window open** - don't close it yet!

---

## Step 4: Start the Data Analyst

The installer should have finished. Now:

1. In the same folder (`Data-Analyst-main`), double-click `start.bat`
2. A black window will open
3. You'll see:
   ```
   Starting IPEDS AI Assistant...
   Launching Gradio interface...
   Running on local URL:  http://127.0.0.1:7860
   ```

4. Your web browser should open automatically
5. If it doesn't, open your browser and go to: `http://localhost:7860`

✅ The Data Analyst is now running!

---

## Step 5: Use the Data Analyst

You should see a web page with:
- A title: "IPEDS Data AI Assistant"
- A text box where you can type questions
- Some example questions below

### Try Asking a Question

In the text box, type:
```
How many students are in the database?
```

Click **"Submit"** and wait a few seconds.

You'll see:
1. The SQL code it generated
2. The results
3. An explanation in plain English

### More Questions to Try

- "What are the retention rates by race and ethnicity?"
- "Show me average GPA by class year"
- "How many students graduated?"

---

## How to Stop the Data Analyst

When you're done:
1. Go to the black Command Prompt window
2. Press `Ctrl + C` on your keyboard
3. The window will close
4. The web page will stop working (this is normal)

---

## How to Start It Again Later

1. Open the `Data-Analyst-main` folder
2. Double-click `start.bat`
3. Wait for the black window to say "Running on local URL..."
4. Open your browser to: `http://localhost:7860`

---

## Troubleshooting

### "Python is not recognized"

**Problem:** Python isn't installed correctly.

**Solution:**
1. Uninstall Python (go to Settings → Apps → Python → Uninstall)
2. Reinstall Python following Step 1 above
3. **Make sure** to check "Add Python to PATH" during installation

---

### "setup.bat won't run"

**Problem:** Windows is blocking the file.

**Solution:**
1. Right-click on `setup.bat`
2. Choose **Properties**
3. At the bottom, check **"Unblock"**
4. Click **OK**
5. Try double-clicking it again

---

### "Port already in use"

**Problem:** Something else is using port 7860.

**Solution:**
1. Restart your computer
2. Try running `start.bat` again

---

### "Can't connect to http://localhost:7860"

**Problem:** The server didn't start correctly.

**Solution:**
1. Make sure the black Command Prompt window is still open
2. Look for the line: "Running on local URL: http://127.0.0.1:7860"
3. If you don't see it, close everything and run `start.bat` again

---

### Still Having Problems?

1. Make sure you have Python 3.8 or newer: `python --version`
2. Make sure you're in the right folder (`Data-Analyst-main`)
3. Try restarting your computer and starting from Step 3

---

## Adding Your OpenAI API Key Later

If you skipped entering the API key during installation:

1. Open the `Data-Analyst-main` folder
2. Find the file named `.env` (it might be hidden)
   - To see hidden files: Open the folder, click **View** menu, check **"Hidden items"**
3. Right-click on `.env` and choose **"Edit with Notepad"**
4. Find the line: `OPENAI_API_KEY=...`
5. Replace everything after the `=` with your actual key
6. Save the file (Ctrl+S)
7. Close Notepad
8. Run `start.bat` again

---

## Summary

**To install:**
1. Install Python (check "Add to PATH")
2. Download and extract the ZIP file
3. Double-click `setup.bat`
4. Wait 5-10 minutes

**To use:**
1. Double-click `start.bat`
2. Open browser to `http://localhost:7860`
3. Type questions and get answers!

**To stop:**
- Press `Ctrl+C` in the black window

---

That's it! You're ready to analyze student data! 🎉
