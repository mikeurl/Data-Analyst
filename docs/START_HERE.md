# 🚀 START HERE - Get Running in 5 Minutes

Having trouble getting the web page to open? **This will fix everything.**

---

## Quick Fix (One Command)

### Mac / Linux:
```bash
./fix_and_launch.sh
```

### Windows:
```cmd
fix_and_launch.bat
```

**That's it!** This will:
1. ✅ Install all packages
2. ✅ Create the database
3. ✅ Generate sample data
4. ✅ Launch the web page

Total time: **~5 minutes**

---

## What to Expect

You'll see output like this:

```
========================================================================
FIX & LAUNCH - Get the AI Assistant running in 5 minutes
========================================================================

Step 1: Activating virtual environment...
✓ Virtual environment activated

Step 2: Installing packages...
This will take 2-3 minutes. Please wait...
[downloading packages...]
✓ Packages installed

Step 3: Configuring API key...
⚠ Using placeholder API key

Step 4: Creating database...
Creating database schema...
Database schema created or verified in 'ipeds_data.db'.

Generating sample data (this takes ~30 seconds)...
Done! Total unique students: 2000
✓ Database created with sample data

========================================================================
LAUNCHING AI ASSISTANT
========================================================================

Starting web server on http://localhost:7860

Running on local URL:  http://127.0.0.1:7860
```

---

## Open the Web Page

**The web page should open automatically.** If not:

1. Look for this line in the output:
   ```
   Running on local URL:  http://127.0.0.1:7860
   ```

2. **Copy that URL** and paste it into your web browser

3. Or just type: **http://localhost:7860**

---

## If It Still Doesn't Work

### Problem: "Port already in use"

**Solution:** Another program is using port 7860.

```bash
# Kill whatever is using port 7860
lsof -i :7860
kill -9 <PID>

# Or edit ai_sql_python_assistant.py and change:
# server_port=7860 to server_port=7861
```

---

### Problem: "Can't connect to page"

**Make sure:**
1. The script is still running (didn't exit with an error)
2. You're opening http://localhost:7860 (not https)
3. Your firewall isn't blocking Python

**Try:**
```bash
curl http://localhost:7860
```
If you see HTML, it's working. The problem is your browser.

---

### Problem: "ModuleNotFoundError: No module named 'openai'"

**Solution:** Packages aren't installed.

```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: "Database file not found"

**Solution:** Database wasn't created.

```bash
python create_ipeds_db_schema.py
python SyntheticDataforSchema2.py
```

---

## Adding Your OpenAI API Key (Optional)

The AI features won't work with the placeholder key. To fix:

1. **Stop the server** (press Ctrl+C)

2. **Get an API key** from https://platform.openai.com/api-keys

3. **Edit the .env file:**
   ```bash
   nano .env
   ```

4. **Replace the placeholder:**
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

5. **Save and run again:**
   ```bash
   ./fix_and_launch.sh
   ```

---

## Manual Launch (If Script Doesn't Work)

If `fix_and_launch.sh` doesn't work, do it manually:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install packages
pip install -r requirements.txt

# 3. Create database
python create_ipeds_db_schema.py
python SyntheticDataforSchema2.py

# 4. Launch
python ai_sql_python_assistant.py
```

Then open http://localhost:7860 in your browser.

---

## Still Stuck?

Run the diagnostic:
```bash
./test_launch.sh
```

This will tell you exactly what's wrong.

---

## Summary

**Easiest way:**
1. Run `./fix_and_launch.sh` (Mac/Linux) or `fix_and_launch.bat` (Windows)
2. Wait 5 minutes
3. Open http://localhost:7860

**That's it!**
