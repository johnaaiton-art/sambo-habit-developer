# Advanced Configuration Guide

This document covers advanced setup options and customizations for the Sambo Bot.

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `GOOGLE_SHEET_ID` | Google Sheet ID from URL | `1a2b3c4d5e6f7g8h9i0j` |
| `GOOGLE_CREDENTIALS_JSON` | Service account JSON (single line) | `{"type":"service_account",...}` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | `sk-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_BASE_URL` | DeepSeek API endpoint | `https://api.deepseek.com` |

## Customizing Habits

To modify the habits tracked by the bot, edit the `HABITS` dictionary in `bot.py`:

```python
HABITS = {
    1: "Your Custom Habit 1",
    2: "Your Custom Habit 2",
    3: "Your Custom Habit 3",
    4: "Your Custom Habit 4",
    5: "Your Custom Habit 5"
}

DAILY_HABITS = {1, 2, 3}  # Which habits are daily
WEEKLY_HABITS = {4, 5}    # Which habits are weekly
```

Then redeploy to Railway.

## Customizing Schedule

The bot uses Moscow timezone by default. To change:

1. Edit the `MOSCOW_TZ` variable in `bot.py`:
   ```python
   MOSCOW_TZ = ZoneInfo("Europe/Moscow")  # Change to your timezone
   ```

2. Modify the schedule in the `run()` method:
   ```python
   # Change the day (0=Monday, 6=Sunday) and time
   job_queue.run_daily(
       self.send_weekly_feedback,
       time=datetime.strptime("19:20", "%H:%M").time(),
       days=[5],  # Saturday
       tzinfo=MOSCOW_TZ
   )
   ```

## Customizing Feedback

The feedback generation uses a prompt sent to DeepSeek. To customize:

1. Edit the `_generate_feedback()` method in `bot.py`
2. Modify the `prompt` variable to change how feedback is generated
3. Adjust the DeepSeek parameters:
   - `temperature`: 0-2 (higher = more creative, lower = more consistent)
   - `max_tokens`: Maximum length of response

## Database Alternatives

Currently, the bot uses Google Sheets. To use a different database:

### PostgreSQL

1. Install PostgreSQL driver: `pip install psycopg2-binary`
2. Create a new class `PostgresDB` with methods:
   - `record_habit(user_id, habit_id)`
   - `get_weekly_stats(user_id)`
   - `get_previous_weeks_stats(user_id)`
3. Replace Google Sheets calls in `SamboBot` class

### MongoDB

1. Install MongoDB driver: `pip install pymongo`
2. Create a new class `MongoDBStore` with similar methods
3. Update `SamboBot` to use MongoDB instead of Google Sheets

## API Integration

### Using Different LLM Provider

To use OpenAI, Claude, or other LLM providers instead of DeepSeek:

1. Update the `_generate_feedback()` method
2. Change the API endpoint and headers
3. Adjust the request/response format

Example for OpenAI:

```python
def _generate_feedback(self, user_id, stats, previous_stats):
    import openai
    
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    
    return response['choices'][0]['message']['content']
```

## Scaling Considerations

### Multiple Users

The current implementation supports multiple users automatically. Each user's data is tracked separately in the Google Sheet.

### Performance Optimization

For large numbers of users:

1. **Batch Processing**: Modify `send_weekly_feedback()` to send messages in batches
2. **Caching**: Cache user data to reduce API calls
3. **Database Indexing**: Add indexes to Google Sheets or switch to a database

### Rate Limiting

Be aware of API rate limits:

- **Telegram**: ~30 messages per second per bot
- **Google Sheets**: ~500 requests per 100 seconds
- **DeepSeek**: Check your plan limits

## Security Enhancements

### Encrypting Credentials

For production, consider encrypting sensitive data:

```python
from cryptography.fernet import Fernet

# Generate key once and store securely
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt credentials
encrypted = cipher.encrypt(credentials.encode())

# Decrypt when needed
decrypted = cipher.decrypt(encrypted).decode()
```

### Input Validation

Add stricter validation for user inputs:

```python
def _validate_habit_id(self, habit_id):
    if not isinstance(habit_id, int):
        return False
    if habit_id < 1 or habit_id > 5:
        return False
    return True
```

### Rate Limiting per User

Prevent abuse by limiting entries per user:

```python
def _check_rate_limit(self, user_id):
    # Check if user has submitted too many entries today
    today = self._get_moscow_now().strftime("%Y-%m-%d")
    # Implementation depends on your database
```

## Monitoring and Logging

### Enhanced Logging

The bot includes basic logging. For production, consider:

1. **Sentry Integration**: Track errors in production
   ```python
   import sentry_sdk
   sentry_sdk.init("your-sentry-dsn")
   ```

2. **Log Aggregation**: Send logs to a service like LogRocket or Datadog

3. **Metrics**: Track bot performance with Prometheus

### Health Checks

Add a health check endpoint:

```python
from flask import Flask
app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'ok'}, 200
```

## Backup and Recovery

### Automated Backups

1. **Google Sheets**: Automatically backed up by Google
2. **Local Backup**: Periodically download your sheet as CSV

```python
def backup_sheet(self):
    worksheet = self.sheet.sheet1
    data = worksheet.get_all_values()
    
    import csv
    with open(f'backup_{datetime.now().isoformat()}.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(data)
```

### Data Recovery

To restore from backup:

1. Create a new Google Sheet
2. Import the CSV file
3. Update `GOOGLE_SHEET_ID` in Railway variables

## Testing

### Local Testing

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt

# Run with test data
export TELEGRAM_BOT_TOKEN=test_token
python bot.py
```

### Unit Tests

Create `test_bot.py`:

```python
import unittest
from bot import SamboBot

class TestSamboBot(unittest.TestCase):
    def setUp(self):
        self.bot = SamboBot()
    
    def test_habit_validation(self):
        success, msg = self.bot._record_habit(123, 1)
        self.assertTrue(success)
    
    def test_invalid_habit(self):
        success, msg = self.bot._record_habit(123, 99)
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
```

## Troubleshooting Advanced Issues

### Memory Leaks

Monitor memory usage:

```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024} MB")
```

### API Timeout Issues

Increase timeout for slow connections:

```python
response = requests.post(
    url,
    headers=headers,
    json=data,
    timeout=60  # Increase from default 30
)
```

### Timezone Issues

Verify timezone handling:

```python
from zoneinfo import ZoneInfo
moscow = ZoneInfo("Europe/Moscow")
print(datetime.now(moscow))
```

## Performance Tips

1. **Cache API responses**: Store results to avoid repeated calls
2. **Use async operations**: Consider using `asyncio` for concurrent operations
3. **Optimize database queries**: Use indexes and efficient queries
4. **Batch operations**: Process multiple users in batches

## Future Enhancements

Potential improvements for advanced users:

- Web dashboard for statistics
- Mobile app integration
- Voice command support
- Photo/video proof of completion
- Social features (share progress with friends)
- Integration with fitness trackers
- Machine learning for habit predictions
