# Installing the IPEDS Data Analyst - Mac

A complete, step-by-step guide for beginners. No experience needed!

---

## What You Need

1. A Mac computer (macOS 10.15 or newer)
2. About 10 minutes
3. Internet connection

---

## Step 1: Install Python

Python is the programming language this tool uses.

### Check if Python is Already Installed

1. Click the **magnifying glass** icon in the top-right corner (Spotlight)
2. Type: `terminal`
3. Click on **Terminal** (it has a black square icon)
4. A white or black window will open. Type: `python3 --version` and press **Enter**

**If you see something like "Python 3.11.5":**
- Great! Python is already installed. Skip to Step 2.

**If you see an error or "command not found":**
- Continue below to install Python.

### Install Python Using Homebrew (Recommended)

Homebrew is a tool that makes installing programs easy on Mac.

#### First, Install Homebrew

1. In Terminal, copy and paste this command:
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Press **Enter**
3. It might ask for your Mac password - type it (nothing will show up, this is normal)
4. Press **Enter**
5. Wait 5-10 minutes for it to install
6. You'll see "Installation successful!"

#### Then, Install Python

1. In Terminal, type:
   ```
   brew install python3
   ```
2. Press **Enter**
3. Wait 2-3 minutes for it to install

### Verify Python Installed

1. In Terminal, type: `python3 --version` and press **Enter**
2. You should see: `Python 3.11.5` (or similar)

✅ Python is now installed!

---

## Step 2: Download the Data Analyst Tool

1. Open your web browser (Safari, Chrome, etc.)
2. Go to: https://github.com/mikeurl/Data-Analyst
3. Click the green **"Code"** button
4. Click **"Download ZIP"**
5. Wait for download to complete
6. Go to your **Downloads** folder (in Finder)
7. Double-click on `Data-Analyst-main.zip` to extract it
8. A new folder will appear called `Data-Analyst-main`

✅ Files are downloaded!

---

## Step 3: Run the Installer

### Open Terminal in the Downloaded Folder

1. Open **Finder**
2. Go to **Downloads**
3. Find the `Data-Analyst-main` folder
4. **Right-click** on the folder
5. Choose **"New Terminal at Folder"**
   - If you don't see this option, hold **Option** key, then right-click, and choose **"New Terminal at Folder"**

A Terminal window will open.

### Run the Setup Script

1. In the Terminal window, type:
   ```
   chmod +x setup.sh
   ```
2. Press **Enter**
3. Then type:
   ```
   ./setup.sh
   ```
4. Press **Enter**

### What You'll See

```
========================================================================
 IPEDS Data Analysis Toolkit - Mac Quick Installer
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

**Keep the Terminal window open** - don't close it yet!

---

## Step 4: Start the Data Analyst

In the same Terminal window, type:
```
./start.sh
```

Press **Enter**.

You'll see:
```
Starting IPEDS AI Assistant...
Launching Gradio interface...
Running on local URL:  http://127.0.0.1:7860
```

Your web browser should open automatically to the Data Analyst page.

If it doesn't open automatically:
1. Open your web browser
2. Go to: `http://localhost:7860`

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
1. Go to the Terminal window
2. Press `Control + C` on your keyboard (not Command!)
3. The Terminal will show a message and return to the prompt
4. The web page will stop working (this is normal)

---

## How to Start It Again Later

1. Open **Finder**
2. Go to **Downloads** → **Data-Analyst-main**
3. **Right-click** on the folder
4. Choose **"New Terminal at Folder"**
5. Type: `./start.sh` and press **Enter**
6. Open your browser to: `http://localhost:7860`

---

## Troubleshooting

### "python3: command not found"

**Problem:** Python isn't installed.

**Solution:**
1. Install Homebrew (see Step 1)
2. Run: `brew install python3`
3. Try the installer again

---

### "Permission denied: ./setup.sh"

**Problem:** The script doesn't have permission to run.

**Solution:**
1. Type: `chmod +x setup.sh` and press **Enter**
2. Then type: `./setup.sh` and press **Enter**

---

### "Port already in use"

**Problem:** Something else is using port 7860.

**Solution:**
1. In Terminal, type: `lsof -i :7860` and press **Enter**
2. You'll see a number under "PID"
3. Type: `kill -9 [PID]` (replace [PID] with the actual number)
4. Try running `./start.sh` again

---

### "Can't connect to http://localhost:7860"

**Problem:** The server didn't start correctly.

**Solution:**
1. Make sure the Terminal window is still open
2. Look for the line: "Running on local URL: http://127.0.0.1:7860"
3. If you don't see it, press Control+C and run `./start.sh` again

---

### "New Terminal at Folder" option is missing

**Problem:** Older macOS version.

**Solution - Method 1:**
1. Open **Terminal** from Spotlight
2. Type: `cd ~/Downloads/Data-Analyst-main` and press **Enter**
3. Continue with the installation

**Solution - Method 2:**
1. Open **System Preferences** → **Keyboard** → **Shortcuts**
2. Click **Services**
3. Check the box next to "New Terminal at Folder"

---

### Still Having Problems?

1. Make sure you have Python 3.8 or newer: `python3 --version`
2. Make sure you're in the right folder (Data-Analyst-main)
3. Try restarting your Mac and starting from Step 3

---

## Adding Your OpenAI API Key Later

If you skipped entering the API key during installation:

1. Open **Finder**
2. Go to **Downloads** → **Data-Analyst-main**
3. Press **Command + Shift + .** (period) to show hidden files
4. Find the file named `.env`
5. Right-click on it and choose **"Open With"** → **"TextEdit"**
6. Find the line: `OPENAI_API_KEY=...`
7. Replace everything after the `=` with your actual key
8. Press **Command + S** to save
9. Close TextEdit
10. Run `./start.sh` again

---

## Summary

**To install:**
1. Install Python via Homebrew
2. Download and extract the ZIP file
3. Open Terminal in the folder
4. Run `chmod +x setup.sh` then `./setup.sh`
5. Wait 5-10 minutes

**To use:**
1. Open Terminal in the Data-Analyst-main folder
2. Run `./start.sh`
3. Open browser to `http://localhost:7860`
4. Type questions and get answers!

**To stop:**
- Press `Control+C` in the Terminal window

---

That's it! You're ready to analyze student data! 🎉
