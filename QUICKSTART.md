# Quick Start Guide

Get your Sambo Bot running in 15 minutes!

## 5-Minute Setup

### 1. Get Your Credentials (5 min)

**Telegram Bot Token**
- Message [@BotFather](https://t.me/botfather) on Telegram
- Send `/newbot`
- Follow prompts, get your token

**Google Sheet ID**
- Create a new sheet at [sheets.google.com](https://sheets.google.com)
- Copy the ID from the URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

**Google Credentials**
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create project → Enable Google Sheets API → Create service account
- Download JSON file
- Share your Google Sheet with the service account email

**DeepSeek API Key**
- Sign up at [DeepSeek](https://platform.deepseek.com/)
- Generate API key

## Deploy to Railway (10 min)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/sambo-bot.git
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to [Railway.app](https://railway.app/)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your sambo-bot repository
5. Railway auto-detects Dockerfile and deploys

### Step 3: Set Environment Variables
In Railway dashboard:
1. Click your service
2. Go to "Variables"
3. Add:
   - `TELEGRAM_BOT_TOKEN` = your token
   - `GOOGLE_SHEET_ID` = your sheet ID
   - `GOOGLE_CREDENTIALS_JSON` = your JSON (single line)
   - `DEEPSEEK_API_KEY` = your API key

## Test It!

1. Open Telegram and find your bot
2. Send `/start`
3. Send `1` (test logging prayer)
4. Bot should respond: "✓ Prayer with first water recorded!"
5. Check your Google Sheet - you should see the entry

## How to Use

Send numbers to log habits:
- `1` - Prayer with first water
- `2` - Qi Gong routine
- `3` - Freestyling on the ball
- `4` - 20 minute run and stretch
- `5` - Strengthening and stretching

Every Saturday at 19:20 Moscow time, get AI-powered feedback!

## Troubleshooting

**Bot not responding?**
- Check Railway logs (click service → View Logs)
- Verify bot token is correct
- Make sure service is "Running"

**Data not in sheet?**
- Check Sheet ID is correct
- Verify service account has access
- Check credentials are single-line JSON

**No Saturday feedback?**
- Wait until 19:20 Moscow time
- Check bot is still running
- Verify DeepSeek API key works

## Next Steps

- Read `README.md` for full documentation
- Check `SETUP_GUIDE.md` for detailed setup
- See `ADVANCED_CONFIG.md` for customization

## Need Help?

- Check the troubleshooting sections in README.md
- Review Railway logs for error messages
- Verify all credentials are correct

---

**That's it! Your bot is now running and tracking your Sambo habits.** 🥋
