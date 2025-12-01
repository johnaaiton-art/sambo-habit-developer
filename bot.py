"""
Sambo Habits Tracking Telegram Bot
Tracks daily and weekly habits with Google Sheets integration and DeepSeek feedback
"""

import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
import requests

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
HABITS = {
    1: "Prayer with first water",
    2: "Qi Gong routine",
    3: "Freestyling on the ball",
    4: "20 minute run and stretch",
    5: "Strengthening and stretching session"
}

DAILY_HABITS = {1, 2, 3}
WEEKLY_HABITS = {4, 5}

class SamboBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        # Initialize Google Sheets
        self.gs_client = self._init_google_sheets()
        self.sheet = None
        
    def _init_google_sheets(self):
        """Initialize Google Sheets client with service account credentials"""
        try:
            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
            if not creds_json:
                logger.error("GOOGLE_CREDENTIALS_JSON not set")
                return None
            
            if not self.sheet_id:
                logger.error("GOOGLE_SHEET_ID not set")
                return None
                
            creds_dict = json.loads(creds_json)
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets', 
                       'https://www.googleapis.com/auth/drive']
            )
            client = gspread.authorize(credentials)
            self.sheet = client.open_by_key(self.sheet_id)
            logger.info("Google Sheets initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            return None

    def _get_moscow_now(self):
        """Get current time in Moscow timezone"""
        return datetime.now(MOSCOW_TZ)

    def _get_week_start(self, date=None):
        """Get Monday of the current week"""
        if date is None:
            date = self._get_moscow_now()
        
        # Monday is 0, Sunday is 6
        days_since_monday = date.weekday()
        week_start = date - timedelta(days=days_since_monday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    def _get_week_number(self, date=None):
        """Get week number for tracking"""
        if date is None:
            date = self._get_moscow_now()
        week_start = self._get_week_start(date)
        return week_start.strftime("%Y-%m-%d")

    def _ensure_sheet_structure(self):
        """Ensure Google Sheet has proper structure"""
        try:
            worksheet = self.sheet.sheet1
            
            # Check if headers exist
            headers = worksheet.row_values(1)
            expected_headers = [
                "Date", "Prayer", "Qi Gong", "Ball", "Run/Stretch", 
                "Strength/Stretch", "Week Number", "Goals from Last Week"
            ]
            
            if headers != expected_headers:
                # Clear and set headers
                worksheet.clear()
                worksheet.append_row(expected_headers)
                logger.info("Sheet structure initialized")
        except Exception as e:
            logger.error(f"Failed to ensure sheet structure: {e}")

    def _get_user_row(self, user_id, week_number):
        """Get or create user's row for the week"""
        try:
            worksheet = self.sheet.sheet1
            
            # Find existing row for this user and week
            user_rows = worksheet.findall(str(user_id))
            for cell in user_rows:
                row_data = worksheet.row_values(cell.row)
                if len(row_data) > 6 and row_data[6] == week_number:
                    return cell.row, row_data
            
            # Create new row
            new_row = [str(user_id), "", "", "", "", "", week_number, ""]
            worksheet.append_row(new_row)
            return worksheet.row_count, new_row
        except Exception as e:
            logger.error(f"Failed to get user row: {e}")
            return None, None

    def _record_habit(self, user_id, habit_id):
        """Record a completed habit"""
        try:
            if habit_id not in HABITS:
                return False, f"Invalid habit number. Use 1-5."
            
            week_number = self._get_week_number()
            row_num, row_data = self._get_user_row(user_id, week_number)
            
            if row_num is None:
                return False, "Failed to record habit"
            
            # Column mapping: Date=1, Prayer=2, QiGong=3, Ball=4, Run=5, Strength=6
            col_map = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
            col = col_map[habit_id]
            
            # Check for duplicates
            worksheet = self.sheet.sheet1
            current_value = worksheet.cell(row_num, col).value
            
            if current_value:
                return False, f"{HABITS[habit_id]} already recorded today"
            
            # Record the habit with today's date
            today = self._get_moscow_now().strftime("%Y-%m-%d")
            worksheet.update_cell(row_num, 1, today)  # Update date
            worksheet.update_cell(row_num, col, "✓")  # Mark as done
            
            return True, f"✓ {HABITS[habit_id]} recorded!"
        except Exception as e:
            logger.error(f"Failed to record habit: {e}")
            return False, "Error recording habit"

    def _get_weekly_stats(self, user_id):
        """Get statistics for the current week"""
        try:
            week_number = self._get_week_number()
            worksheet = self.sheet.sheet1
            
            # Find all rows for this user in current week
            stats = {
                1: 0,  # Prayer
                2: 0,  # Qi Gong
                3: 0,  # Ball
                4: 0,  # Run
                5: 0   # Strength
            }
            
            all_rows = worksheet.get_all_values()
            for row_idx, row in enumerate(all_rows[1:], start=2):  # Skip header
                if len(row) > 6 and row[6] == week_number:
                    # Check each habit column
                    for habit_id in range(1, 6):
                        col = habit_id + 1
                        if col < len(row) and row[col] == "✓":
                            stats[habit_id] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get weekly stats: {e}")
            return None

    def _get_previous_weeks_stats(self, user_id, weeks_back=3):
        """Get statistics from previous weeks"""
        try:
            worksheet = self.sheet.sheet1
            all_rows = worksheet.get_all_values()
            
            previous_stats = {}
            current_date = self._get_moscow_now()
            
            for week_offset in range(1, weeks_back + 1):
                week_date = current_date - timedelta(weeks=week_offset)
                week_number = self._get_week_number(week_date)
                
                stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                
                for row in all_rows[1:]:
                    if len(row) > 6 and row[6] == week_number:
                        for habit_id in range(1, 6):
                            col = habit_id + 1
                            if col < len(row) and row[col] == "✓":
                                stats[habit_id] += 1
                
                previous_stats[week_number] = stats
            
            return previous_stats
        except Exception as e:
            logger.error(f"Failed to get previous weeks stats: {e}")
            return {}

    def _get_last_week_goals(self, user_id):
        """Get goals set for this week"""
        try:
            week_number = self._get_week_number()
            worksheet = self.sheet.sheet1
            all_rows = worksheet.get_all_values()
            
            for row in all_rows[1:]:
                if len(row) > 7 and row[6] == week_number:
                    return row[7] if row[7] else None
            
            return None
        except Exception as e:
            logger.error(f"Failed to get last week goals: {e}")
            return None

    def _generate_feedback(self, user_id, stats, previous_stats):
        """Generate feedback using DeepSeek API"""
        try:
            # Prepare data for DeepSeek
            current_week = self._get_week_number()
            
            # Calculate statistics
            daily_completion = {h: stats[h] for h in DAILY_HABITS}
            weekly_completion = {h: stats[h] for h in WEEKLY_HABITS}
            
            # Get previous week's stats for comparison
            prev_week_date = self._get_moscow_now() - timedelta(weeks=1)
            prev_week_number = self._get_week_number(prev_week_date)
            prev_stats = previous_stats.get(prev_week_number, {})
            
            # Get goals from last week
            last_goals = self._get_last_week_goals(user_id)
            
            prompt = f"""
Analyze the Sambo training habits for the week of {current_week}:

Current Week Statistics:
- Prayer with first water: {daily_completion[1]}/6 days
- Qi Gong routine: {daily_completion[2]}/6 days
- Freestyling on the ball: {daily_completion[3]}/6 days
- 20 minute run and stretch: {weekly_completion[4]}/1 session
- Strengthening and stretching: {weekly_completion[5]}/1 session

Previous Week Statistics:
- Prayer: {prev_stats.get(1, 0)}/6 days
- Qi Gong: {prev_stats.get(2, 0)}/6 days
- Ball: {prev_stats.get(3, 0)}/6 days
- Run: {prev_stats.get(4, 0)}/1 session
- Strength: {prev_stats.get(5, 0)}/1 session

Goals from Last Week: {last_goals or "None set"}

Please provide:
1. A clear summary of this week's performance
2. Comparison to last week - what improved or declined
3. If any habit declined or didn't reach maximum, ask for an improvement plan
4. Reference any goals mentioned from last week and whether they were achieved
5. Keep tone encouraging but honest

Format the response in a friendly, engaging way for a Telegram message.
"""
            
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.deepseek_base_url}/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                feedback = result['choices'][0]['message']['content']
                return feedback
            else:
                logger.error(f"DeepSeek API error: {response.status_code}")
                return self._generate_default_feedback(stats, prev_stats)
        except Exception as e:
            logger.error(f"Failed to generate feedback: {e}")
            return self._generate_default_feedback(stats, prev_stats)

    def _generate_default_feedback(self, stats, prev_stats):
        """Generate default feedback if API fails"""
        feedback = "📊 **Weekly Summary**\n\n"
        
        for habit_id in range(1, 6):
            current = stats.get(habit_id, 0)
            previous = prev_stats.get(habit_id, 0)
            habit_name = HABITS[habit_id]
            
            if habit_id in DAILY_HABITS:
                feedback += f"• {habit_name}: {current}/6 days"
            else:
                feedback += f"• {habit_name}: {current}/1 session"
            
            if previous > 0:
                if current > previous:
                    feedback += " ⬆️ (improved)"
                elif current < previous:
                    feedback += " ⬇️ (declined)"
                else:
                    feedback += " ➡️ (same)"
            
            feedback += "\n"
        
        return feedback

    def _should_ask_for_goals(self, stats, prev_stats):
        """Determine if we should ask for improvement goals"""
        for habit_id in range(1, 6):
            current = stats.get(habit_id, 0)
            previous = prev_stats.get(habit_id, 0)
            
            # Max values
            max_val = 6 if habit_id in DAILY_HABITS else 1
            
            # Ask if declined or didn't improve and not at max
            if current < previous or (current == previous and current < max_val):
                return True
        
        return False

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        await update.message.reply_text(
            "🥋 Welcome to Sambo Habits Tracker!\n\n"
            "Send me a number (1-5) to log your habits:\n"
            "1 - Prayer with first water\n"
            "2 - Qi Gong routine\n"
            "3 - Freestyling on the ball\n"
            "4 - 20 minute run and stretch\n"
            "5 - Strengthening and stretching\n\n"
            "Send each number separately. Sunday is a rest day."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Check if it's a number
        if not text.isdigit():
            await update.message.reply_text("Please send a number (1-5)")
            return
        
        habit_id = int(text)
        success, message = self._record_habit(user_id, habit_id)
        
        await update.message.reply_text(message)

    async def send_weekly_feedback(self, context: ContextTypes.DEFAULT_TYPE):
        """Send weekly feedback on Saturday at 19:20 Moscow time"""
        # This will be called by the scheduler
        logger.info("Sending weekly feedback")
        
        try:
            # Get all users from sheet
            worksheet = self.sheet.sheet1
            all_rows = worksheet.get_all_values()
            
            users = set()
            for row in all_rows[1:]:
                if row:
                    users.add(int(row[0]))
            
            for user_id in users:
                stats = self._get_weekly_stats(user_id)
                previous_stats = self._get_previous_weeks_stats(user_id, weeks_back=3)
                
                feedback = self._generate_feedback(user_id, stats, previous_stats)
                
                # Send feedback
                await context.bot.send_message(
                    chat_id=user_id,
                    text=feedback,
                    parse_mode="Markdown"
                )
                
                # Ask for goals if needed
                if self._should_ask_for_goals(stats, previous_stats):
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="📝 What's your plan to improve next week? Reply with your goals."
                    )
        except Exception as e:
            logger.error(f"Failed to send weekly feedback: {e}")

    async def handle_goal_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle goal input from user"""
        user_id = update.effective_user.id
        goal_text = update.message.text
        
        try:
            week_number = self._get_week_number()
            worksheet = self.sheet.sheet1
            
            # Find user's row for this week
            all_rows = worksheet.get_all_values()
            for row_idx, row in enumerate(all_rows[1:], start=2):
                if len(row) > 6 and row[6] == week_number:
                    # Update goals column (index 7)
                    worksheet.update_cell(row_idx, 8, goal_text)
                    await update.message.reply_text("✓ Goals recorded for next week!")
                    return
        except Exception as e:
            logger.error(f"Failed to record goals: {e}")
        
        await update.message.reply_text("Error recording goals")

    def run(self):
        """Start the bot"""
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            return
        
        app = Application.builder().token(self.bot_token).build()
        
        # Handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Schedule weekly feedback if job queue is available
        try:
            job_queue = app.job_queue
            if job_queue:
                job_queue.run_daily(
                    self.send_weekly_feedback,
                    time=datetime.strptime("19:20", "%H:%M").time(),
                    days=[5],
                    tzinfo=MOSCOW_TZ
                )
                logger.info("Scheduled weekly feedback for Saturday 19:20 Moscow time")
        except Exception as e:
            logger.warning(f"Could not set up job queue: {e}")
        
        logger.info("Bot started and polling for messages...")
        app.run_polling()


if __name__ == "__main__":
    bot = SamboBot()
    bot._ensure_sheet_structure()
    bot.run()
