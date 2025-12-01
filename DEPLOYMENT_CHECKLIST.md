# Deployment Checklist

Use this checklist to ensure everything is properly configured before deploying to Railway.

## Pre-Deployment

### Telegram Setup
- [ ] Created bot with @BotFather
- [ ] Have bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
- [ ] Tested bot responds to `/start` command locally

### Google Sheets Setup
- [ ] Created new Google Sheet
- [ ] Copied Sheet ID from URL
- [ ] Created Google Cloud project
- [ ] Enabled Google Sheets API
- [ ] Created service account
- [ ] Downloaded service account JSON file
- [ ] Shared Google Sheet with service account email
- [ ] Service account has "Editor" access

### DeepSeek Setup
- [ ] Created DeepSeek account
- [ ] Generated API key
- [ ] Verified API key has credits
- [ ] Tested API key works

### Code Preparation
- [ ] All files copied to project folder:
  - [ ] `bot.py`
  - [ ] `requirements.txt`
  - [ ] `Dockerfile`
  - [ ] `railway.toml`
  - [ ] `.env.example`
  - [ ] `.gitignore`
  - [ ] `README.md`
  - [ ] `SETUP_GUIDE.md`
  - [ ] `ADVANCED_CONFIG.md`
- [ ] Git repository initialized
- [ ] All files committed to git

### GitHub Setup
- [ ] Created GitHub repository
- [ ] Pushed code to GitHub
- [ ] Repository is public (or Railway has access)

## Railway Deployment

### Initial Setup
- [ ] Logged in to Railway.app
- [ ] Connected GitHub account
- [ ] Created new project
- [ ] Selected GitHub repository
- [ ] Railway detected Dockerfile

### Environment Variables
- [ ] Set `TELEGRAM_BOT_TOKEN`
- [ ] Set `GOOGLE_SHEET_ID`
- [ ] Set `GOOGLE_CREDENTIALS_JSON` (single line, no breaks)
- [ ] Set `DEEPSEEK_API_KEY`
- [ ] Optional: Set `DEEPSEEK_BASE_URL` if using custom endpoint

### Deployment Verification
- [ ] Service shows "Running" status
- [ ] No errors in deployment logs
- [ ] Service has been running for at least 1 minute

## Post-Deployment Testing

### Bot Functionality
- [ ] Bot responds to `/start` command
- [ ] Can send habit number (1-5) to bot
- [ ] Bot acknowledges with confirmation message
- [ ] No duplicate entries allowed for same habit same day

### Google Sheets Integration
- [ ] Data appears in Google Sheet
- [ ] Sheet structure is correct:
  - [ ] Headers: Date, Prayer, Qi Gong, Ball, Run/Stretch, Strength/Stretch, Week Number, Goals from Last Week
  - [ ] User data in rows
  - [ ] Checkmarks (✓) in habit columns
- [ ] Week number is correct (Monday's date)

### Scheduled Feedback
- [ ] Wait for Saturday 19:20 Moscow time
- [ ] Bot sends feedback message
- [ ] Feedback includes:
  - [ ] Weekly statistics
  - [ ] Comparison to previous weeks
  - [ ] Improvement suggestions (if applicable)
  - [ ] Reference to previous goals (if applicable)

## Monitoring

### Ongoing Checks
- [ ] Check Railway logs weekly for errors
- [ ] Verify bot is still running (status = Running)
- [ ] Check Google Sheet for data accumulation
- [ ] Monitor DeepSeek API usage

### Common Issues to Watch For
- [ ] Bot stops responding (check Railway status)
- [ ] Data not appearing in sheet (check credentials)
- [ ] No feedback on Saturday (check scheduled time)
- [ ] API errors (check API keys and rate limits)

## Maintenance

### Regular Tasks
- [ ] Weekly: Review feedback quality
- [ ] Monthly: Check Google Sheet organization
- [ ] Monthly: Verify Railway service is healthy
- [ ] Quarterly: Review and update habits if needed

### Backup
- [ ] Download Google Sheet as CSV monthly
- [ ] Keep backup of service account JSON file
- [ ] Keep backup of bot token (in secure location)

## Troubleshooting Reference

| Issue | Check |
|-------|-------|
| Bot not responding | Railway status, bot token, logs |
| Data not in sheet | Sheet ID, credentials, permissions |
| No Saturday feedback | Scheduled time, DeepSeek API, bot running |
| Duplicate entries | Check bot.py logic, test locally |
| Wrong timezone | Verify MOSCOW_TZ setting |

## Notes

- Deployment typically takes 2-5 minutes
- First data entry should appear in Google Sheet within seconds
- First Saturday feedback will arrive at 19:20 Moscow time
- Keep all credentials secure and never commit them to GitHub

## Sign-Off

- [ ] All checklist items completed
- [ ] Bot tested and working
- [ ] Ready for production use

**Date Deployed**: _______________
**Deployed By**: _______________
**Notes**: _______________
