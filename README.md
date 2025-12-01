# Sambo Habits Tracking Bot

A Telegram bot that tracks your Sambo training habits with automatic weekly feedback powered by DeepSeek AI. The bot logs your daily and weekly activities to Google Sheets and provides intelligent progress analysis.

## Features

- **Daily Habit Tracking**: Log 3 daily habits (prayer, qi gong, ball freestyling)
- **Weekly Habit Tracking**: Log 2 weekly sessions (running/stretching, strengthening/stretching)
- **Automatic Feedback**: Receives AI-powered feedback every Saturday at 19:20 Moscow time
- **Progress Comparison**: Compares current week performance to previous weeks
- **Goal Setting**: Asks for improvement plans when performance declines
- **Google Sheets Integration**: All data automatically stored and organized
- **Duplicate Prevention**: Prevents logging the same habit twice in one day

## Prerequisites

Before setting up the bot, you'll need:

1. **Telegram Bot Token**
   - Create a bot with [@BotFather](https://t.me/botfather)
   - Get your bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Google Sheets Setup**
   - Create a new Google Sheet
   - Get the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`
   - Create a service account:
     - Go to [Google Cloud Console](https://console.cloud.google.com/)
     - Create a new project
     - Enable Google Sheets API
     - Create a service account and download the JSON credentials
     - Share your Google Sheet with the service account email

3. **DeepSeek API Key**
   - Sign up at [DeepSeek](https://platform.deepseek.com/)
   - Get your API key

## Local Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd sambo-bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CREDENTIALS_JSON={"type": "service_account", ...}
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

**Important**: For `GOOGLE_CREDENTIALS_JSON`, paste the entire JSON content from your service account file as a single-line string.

### 5. Run Locally

```bash
python bot.py
```

The bot will start polling for messages. You can now message your bot on Telegram to test it.

## Deployment on Railway

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Deploy on Railway

1. Go to [Railway.app](https://railway.app/)
2. Sign in with GitHub
3. Create a new project
4. Select "Deploy from GitHub repo"
5. Choose your sambo-bot repository
6. Railway will automatically detect the Dockerfile

### 3. Set Environment Variables

In Railway dashboard:

1. Go to your project
2. Click on the service
3. Go to "Variables" tab
4. Add all environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `GOOGLE_SHEET_ID`
   - `GOOGLE_CREDENTIALS_JSON`
   - `DEEPSEEK_API_KEY`

The bot will automatically start and begin polling.

## How to Use

### Logging Habits

Send a number (1-5) to the bot for each completed habit:

- **1** - Prayer with first water
- **2** - Qi Gong routine
- **3** - Freestyling on the ball
- **4** - 20 minute run and stretch
- **5** - Strengthening and stretching session

**Example**: If you completed qi gong and ball freestyling today, send:
```
2
3
```

Send each number as a separate message. The bot will acknowledge each one.

### Weekly Feedback

Every Saturday at 19:20 Moscow time, the bot will send you:

1. **Weekly Statistics**: How many times you completed each habit
2. **Progress Comparison**: How this week compares to previous weeks
3. **Improvement Suggestions**: If performance declined or didn't improve, the bot asks for your improvement plan
4. **Goal Tracking**: References goals you set from the previous week

### Tracking Schedule

- **Monday 00:00 Moscow time**: Tracking week begins
- **Saturday 19:20 Moscow time**: Feedback sent, week ends
- **Sunday**: Rest day (not tracked)
- **Tracked days**: Monday - Saturday (6 days)

## Google Sheets Structure

The bot automatically creates and maintains the following sheet structure:

| Date | Prayer | Qi Gong | Ball | Run/Stretch | Strength/Stretch | Week Number | Goals from Last Week |
|------|--------|---------|------|-------------|------------------|-------------|----------------------|
| 2025-01-06 | ✓ | ✓ |  | ✓ |  | 2025-01-06 | Focus on ball work |

- **Date**: Last date a habit was logged
- **Habit columns**: Marked with ✓ when completed
- **Week Number**: Monday of that week (YYYY-MM-DD format)
- **Goals from Last Week**: Your improvement plan from the previous week

## Troubleshooting

### Bot not responding
- Check that `TELEGRAM_BOT_TOKEN` is correct
- Ensure the bot is running (check Railway logs)
- Verify internet connection

### Google Sheets not updating
- Confirm `GOOGLE_SHEET_ID` is correct
- Verify the service account has access to the sheet
- Check `GOOGLE_CREDENTIALS_JSON` is properly formatted (single line)

### No feedback on Saturday
- Verify `DEEPSEEK_API_KEY` is correct
- Check that the bot is running at the scheduled time
- Review Railway logs for errors

### DeepSeek API errors
- Confirm API key is valid and has credits
- Check API rate limits
- Verify internet connection

## Project Structure

```
sambo-bot/
├── bot.py                 # Main bot application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration for Railway
├── railway.toml          # Railway deployment config
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Code Overview

### SamboBot Class

The main `SamboBot` class handles:

- **Google Sheets Integration**: Initializes client, manages sheet structure
- **Habit Recording**: Logs completed habits with duplicate prevention
- **Statistics Calculation**: Computes weekly and historical stats
- **Feedback Generation**: Uses DeepSeek API to create intelligent feedback
- **Telegram Integration**: Handles bot commands and messages

### Key Methods

- `_record_habit()`: Records a completed habit
- `_get_weekly_stats()`: Gets current week statistics
- `_get_previous_weeks_stats()`: Gets historical data for comparison
- `_generate_feedback()`: Creates AI-powered feedback using DeepSeek
- `send_weekly_feedback()`: Sends Saturday feedback to all users

## Development Notes

- The bot uses Moscow timezone (`Europe/Moscow`) for all time calculations
- Week starts Monday 00:00 and ends Saturday 23:59
- Sunday is automatically excluded from tracking
- All data is stored in Google Sheets for easy access and backup
- The bot prevents duplicate entries for the same habit on the same day

## Future Enhancements

Possible improvements:

- Add `/stats` command for on-demand statistics
- Support for custom habits
- Weekly email summaries
- Integration with other calendar systems
- Habit streak tracking
- Photo/video proof of completion

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review Railway logs
3. Verify all environment variables are set correctly
4. Check that all prerequisites are installed

## Author

Created for Sambo training habit tracking.
