# Deploying to Hugging Face Spaces

This guide will help you deploy the Higher Education AI Analyst to Hugging Face Spaces for web access.

## Prerequisites

1. A Hugging Face account (free) - Sign up at [huggingface.co](https://huggingface.co)
2. Git installed on your computer
3. Your GitHub repository synced with latest changes

## Deployment Steps

### Option 1: Direct Upload (Easiest)

1. **Go to Hugging Face Spaces**
   - Visit [huggingface.co/spaces](https://huggingface.co/spaces)
   - Click "Create new Space"

2. **Configure your Space**
   - Space name: `higher-ed-ai-analyst` (or your choice)
   - License: Choose appropriate license
   - Select SDK: **Gradio**
   - Click "Create Space"

3. **Upload Files**
   - Click "Files" tab in your new Space
   - Click "Add file" → "Upload files"
   - Upload these files:
     - `app.py`
     - `ai_sql_python_assistant.py`
     - `create_ipeds_db_schema.py`
     - `SyntheticDataforSchema2.py`
     - `requirements.txt`
     - Rename `README_HUGGINGFACE.md` to `README.md` and upload it

4. **Wait for Build**
   - Hugging Face will automatically install dependencies and start your app
   - First startup will take ~2-3 minutes (generating synthetic data)
   - Watch the "Logs" tab for progress

5. **Test Your Space**
   - Once running, you'll see your Gradio interface
   - Get an OpenAI API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Enter the key and try asking a question

### Option 2: Git Push (Advanced)

1. **Clone your Space repository**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/higher-ed-ai-analyst
   cd higher-ed-ai-analyst
   ```

2. **Copy files from this repo**
   ```bash
   cp /path/to/Data-Analyst/app.py .
   cp /path/to/Data-Analyst/ai_sql_python_assistant.py .
   cp /path/to/Data-Analyst/create_ipeds_db_schema.py .
   cp /path/to/Data-Analyst/SyntheticDataforSchema2.py .
   cp /path/to/Data-Analyst/requirements.txt .
   cp /path/to/Data-Analyst/README_HUGGINGFACE.md README.md
   ```

3. **Commit and push**
   ```bash
   git add .
   git commit -m "Initial deployment of Higher Education AI Analyst"
   git push
   ```

4. **Monitor deployment**
   - Visit your Space URL
   - Check the "Logs" tab for build progress

## Files Required for Deployment

| File | Purpose |
|------|---------|
| `app.py` | Entry point for Hugging Face Spaces |
| `ai_sql_python_assistant.py` | Main application code |
| `create_ipeds_db_schema.py` | Database schema creation |
| `SyntheticDataforSchema2.py` | Synthetic data generation |
| `requirements.txt` | Python dependencies |
| `README.md` | Space description (use README_HUGGINGFACE.md) |

## What Happens on Deployment

1. Hugging Face installs all packages from `requirements.txt`
2. Runs `app.py`
3. App detects no database exists
4. Auto-generates database schema and synthetic data (~30 seconds)
5. Launches Gradio interface on port 7860
6. Your Space is live!

## Sharing Your Space

Once deployed, share your Space URL:
```
https://huggingface.co/spaces/YOUR_USERNAME/higher-ed-ai-analyst
```

Users can:
- Access the web interface directly (no installation needed)
- Enter their own OpenAI API key
- Ask questions and get AI-powered analysis
- View the About section for more information

## Important Notes

⚠️ **Privacy**: Each user must bring their own OpenAI API key. Keys are not stored.

⚠️ **Free Tier**: Hugging Face free tier includes:
- 2 CPU cores
- 16GB RAM
- 50GB storage
- Should be sufficient for this app

⚠️ **Persistence**: The database is generated on startup. If the Space restarts, it will regenerate (takes ~30 seconds).

⚠️ **Costs**: You pay for OpenAI API usage based on your API key. Hugging Face hosting is free.

## Troubleshooting

### Build fails with "Module not found"
- Check that `requirements.txt` is uploaded correctly
- Verify all Python files are present

### App crashes on startup
- Check the Logs tab for error messages
- Ensure database generation completes successfully

### Gradio interface doesn't load
- Wait 2-3 minutes for first startup (database generation)
- Check Logs for "Launching Gradio interface..." message

### Questions fail with API errors
- Verify OpenAI API key is correct
- Check API key has credits available at platform.openai.com

## Next Steps

After deployment:
1. Test the interface thoroughly
2. Share the URL with your institutional research colleagues
3. Gather feedback
4. Iterate and improve based on usage

## Support

For issues with:
- **Hugging Face Spaces**: Check [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **This application**: Open an issue at [github.com/mikeurl/Data-Analyst](https://github.com/mikeurl/Data-Analyst)
