# Sambo Bot - Complete Setup Guide

This guide walks you through setting up the Sambo Habits Tracking Bot step-by-step.

## Step 1: Get Your Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/start` to begin
3. Send `/newbot` to create a new bot
4. Follow the prompts:
   - Choose a name for your bot (e.g., "Sambo Habits Tracker")
   - Choose a username (must end with "bot", e.g., "sambo_habits_bot")
5. BotFather will give you a token that looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
6. **Save this token** - you'll need it later

## Step 2: Set Up Google Sheets

### 2.1 Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Click "Create" → "Blank spreadsheet"
3. Name it "Sambo Habits Tracker"
4. In the URL, find the Sheet ID: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`
5. **Save the SHEET_ID** - you'll need it later

### 2.2 Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project:
   - Click the project dropdown at the top
   - Click "NEW PROJECT"
   - Name it "Sambo Bot"
   - Click "CREATE"
3. Enable Google Sheets API:
   - In the search bar, search for "Google Sheets API"
   - Click on it and press "ENABLE"
4. Create a service account:
   - Go to "Credentials" (left sidebar)
   - Click "Create Credentials" → "Service Account"
   - Fill in the form:
     - Service account name: "sambo-bot"
     - Click "CREATE AND CONTINUE"
   - Skip the optional steps and click "DONE"
5. Create a key:
   - Click on the service account you just created
   - Go to "KEYS" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON"
   - Click "CREATE"
   - A JSON file will download - **save this file securely**

### 2.3 Share the Sheet with Service Account

1. Open the JSON file you downloaded
2. Find the `"client_email"` field (looks like: `sambo-bot@project-id.iam.gserviceaccount.com`)
3. Copy this email
4. Go back to your Google Sheet
5. Click "Share" button (top right)
6. Paste the service account email
7. Give it "Editor" access
8. Click "Share"

## Step 3: Get DeepSeek API Key

1. Go to [DeepSeek Platform](https://platform.deepseek.com/)
2. Sign up or log in
3. Go to "API Keys" section
4. Create a new API key
5. **Save this key** - you'll need it later

## Step 4: Prepare Environment Variables

You'll need to convert the JSON credentials file into a single-line string.

### Option A: Using Python (Recommended)

```python
import json

# Read your downloaded JSON file
with open('path/to/your/downloaded/file.json', 'r') as f:
    creds = json.load(f)

# Convert to single-line string
creds_string = json.dumps(creds)
print(creds_string)
```

Copy the output - this is your `GOOGLE_CREDENTIALS_JSON`.

### Option B: Manual

1. Open the JSON file in a text editor
2. Remove all line breaks
3. This is your `GOOGLE_CREDENTIALS_JSON`

## Step 5: Deploy on Railway

### 5.1 Prepare Your Repository

1. Create a folder on your computer for the project
2. Copy all files from the bot project into this folder:
   - `bot.py`
   - `requirements.txt`
   - `Dockerfile`
   - `railway.toml`
   - `.env.example`
   - `.gitignore`
   - `README.md`

3. Initialize Git:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

### 5.2 Push to GitHub

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it "sambo-bot"
3. Follow GitHub's instructions to push your code:
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/sambo-bot.git
   git push -u origin main
   ```

### 5.3 Deploy on Railway

1. Go to [Railway.app](https://railway.app/)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub account
5. Select the "sambo-bot" repository
6. Railway will automatically detect the Dockerfile and start deploying

### 5.4 Set Environment Variables

1. In Railway dashboard, click on your project
2. Click on the service (it should say "sambo-bot")
3. Go to the "Variables" tab
4. Click "New Variable" and add:

   ```
   TELEGRAM_BOT_TOKEN = your_bot_token_here
   GOOGLE_SHEET_ID = your_sheet_id_here
   GOOGLE_CREDENTIALS_JSON = {"type": "service_account", ...}
   DEEPSEEK_API_KEY = your_deepseek_api_key_here
   ```

5. Click "Save"
6. Railway will automatically restart the bot with the new variables

## Step 6: Test Your Bot

1. Open Telegram
2. Search for your bot (the username you created with BotFather)
3. Send `/start` to the bot
4. Send `1` to test logging a habit
5. The bot should respond with "✓ Prayer with first water recorded!"

## Step 7: Check Google Sheets

1. Go back to your Google Sheet
2. You should see a new row with your test entry
3. The sheet structure should be automatically created with headers

## Troubleshooting

### Bot doesn't respond

**Check 1**: Is the bot token correct?
- Go back to BotFather and verify the token
- Make sure there are no extra spaces

**Check 2**: Is the bot deployed?
- Go to Railway dashboard
- Check if the service is running (green status)
- Click "View Logs" to see if there are errors

**Check 3**: Is the bot token set in Railway?
- Go to Variables tab
- Verify `TELEGRAM_BOT_TOKEN` is set correctly

### Google Sheets not updating

**Check 1**: Is the sheet ID correct?
- Go to your Google Sheet
- Copy the ID from the URL again
- Make sure it's set in Railway variables

**Check 2**: Is the service account authorized?
- Check that you shared the sheet with the service account email
- The service account should have "Editor" access

**Check 3**: Is the credentials JSON correct?
- Make sure it's a single line with no line breaks
- Verify it's valid JSON (no missing quotes or commas)

### No feedback on Saturday

**Check 1**: Is the bot still running?
- Check Railway logs
- Verify the service is still active

**Check 2**: Is DeepSeek API key valid?
- Test the API key on DeepSeek platform
- Make sure it has credits

**Check 3**: Check the logs
- Go to Railway dashboard
- Click "View Logs"
- Look for any error messages around the scheduled time

## Next Steps

Once everything is working:

1. Start using the bot to log your habits
2. On Saturday at 19:20 Moscow time, you'll receive feedback
3. The bot will ask for improvement plans if needed
4. Check your Google Sheet to see all your data organized

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review the README.md file
3. Check Railway logs for error messages
4. Verify all credentials are correct and properly formatted

## Security Notes

- Never share your bot token or API keys
- Keep your `.env` file local (don't commit to GitHub)
- The `.gitignore` file prevents accidental commits of sensitive data
- Railway variables are encrypted and secure

## Tips

- You can test the bot locally before deploying to Railway
- To run locally, create a `.env` file with your credentials and run `python bot.py`
- Check your Google Sheet regularly to verify data is being recorded
- You can manually edit the sheet if needed (e.g., to correct entries)
