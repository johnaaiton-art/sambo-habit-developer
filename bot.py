"""
Sambo Habits Tracking Telegram Bot
Tracks daily/weekly habits and consumption habits with Google Sheets integration
"""

import os
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from google.oauth2.service_account import Credentials

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# Sheet 1: Sambo Habits
HABITS = {
    1: "Prayer with first water",
    2: "Qi Gong routine",
    3: "Freestyling on the ball",
    4: "20 minute run and stretch",
    5: "Strengthening and stretching session"
}

DAILY_HABITS = {1, 2, 3}
WEEKLY_HABITS = {4, 5}

# Sheet 2: Consumption Habits
CONSUMPTION_HABITS = {
    'x': "Coffee",
    'y': "Sugary food",
    'z': "Flour-based food"
}

class SamboBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        # Initialize Google Sheets
        self.gs_client = None
        self.sheet = None
        self.consumption_sheet = None
        self._init_google_sheets()
        
        # Track user state for consumption entry
        self.user_states = {}  # user_id -> {'awaiting_type': 'x'/'y'/'z'}
        
    def _init_google_sheets(self):
        """Initialize Google Sheets client with service account credentials"""
        try:
            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
            if not creds_json:
                logger.error("GOOGLE_CREDENTIALS_JSON not set")
                return
            
            if not self.sheet_id:
                logger.error("GOOGLE_SHEET_ID not set")
                return
                
            creds_dict = json.loads(creds_json)
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets', 
                       'https://www.googleapis.com/auth/drive']
            )
            self.gs_client = gspread.authorize(credentials)
            
            # Open the main spreadsheet
            spreadsheet = self.gs_client.open_by_key(self.sheet_id)
            
            # Get or create the two sheets
            try:
                self.sheet = spreadsheet.worksheet("Sheet1")  # Sambo habits
            except gspread.WorksheetNotFound:
                self.sheet = spreadsheet.add_worksheet(title="Sambo Habits", rows=1000, cols=10)
                logger.info("Created Sambo Habits sheet")
            
            try:
                self.consumption_sheet = spreadsheet.worksheet("Consumption")
            except gspread.WorksheetNotFound:
                self.consumption_sheet = spreadsheet.add_worksheet(title="Consumption", rows=1000, cols=10)
                logger.info("Created Consumption sheet")
            
            # Initialize sheet structures
            self._ensure_sheet_structure()
            self._ensure_consumption_sheet_structure()
            
            logger.info("Google Sheets initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            import traceback
            logger.error(traceback.format_exc())

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

    # ========== SHEET 1: SAMBO HABITS ==========
    
    def _ensure_sheet_structure(self):
        """Ensure Sheet1 has proper structure"""
        try:
            if not self.sheet:
                return
            
            # Check if headers exist
            headers = self.sheet.row_values(1)
            expected_headers = [
                "User ID", "Date", "Prayer", "Qi Gong", "Ball", "Run/Stretch", 
                "Strength/Stretch", "Week Number", "Goals from Last Week"
            ]
            
            if headers != expected_headers:
                self.sheet.clear()
                self.sheet.append_row(expected_headers)
                logger.info("Sheet1 structure initialized")
        except Exception as e:
            logger.error(f"Failed to ensure sheet structure: {e}")

    def _get_user_row(self, user_id, week_number):
        """Get or create user's row for the week in Sheet1"""
        try:
            all_rows = self.sheet.get_all_values()
            
            # Find existing row for this user and week
            for row_idx, row in enumerate(all_rows[1:], start=2):  # Skip header
                if len(row) > 7:
                    # Check User ID (col 0) and Week Number (col 7)
                    if row[0] == str(user_id) and row[7] == week_number:
                        return row_idx, row
            
            # Create new row
            new_row = [str(user_id), "", "", "", "", "", "", week_number, ""]
            self.sheet.append_row(new_row)
            return self.sheet.row_count, new_row
        except Exception as e:
            logger.error(f"Failed to get user row: {e}")
            return None, None

    def _record_habit(self, user_id, habit_id):
        """Record a completed habit in Sheet1"""
        try:
            if not self.sheet:
                logger.error("Sheet not initialized")
                return False, "Sheet not initialized"
            
            if habit_id not in HABITS:
                return False, f"Invalid habit number. Use 1-5."
            
            week_number = self._get_week_number()
            row_num, row_data = self._get_user_row(user_id, week_number)
            
            if row_num is None:
                logger.error(f"Failed to get row for user {user_id}")
                return False, "Failed to record habit"
            
            # Column mapping: UserID=1, Date=2, Prayer=3, QiGong=4, Ball=5, Run=6, Strength=7
            col_map = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7}
            col = col_map[habit_id]
            
            # Check for duplicates
            current_value = self.sheet.cell(row_num, col).value
            
            if current_value:
                return False, f"{HABITS[habit_id]} already recorded today"
            
            # Record the habit with today's date
            today = self._get_moscow_now().strftime("%Y-%m-%d")
            self.sheet.update_cell(row_num, 2, today)  # Update date column
            self.sheet.update_cell(row_num, col, "✓")  # Mark as done
            
            logger.info(f"Recorded habit {habit_id} for user {user_id} in row {row_num}, col {col}")
            return True, f"✓ {HABITS[habit_id]} recorded!"
        except Exception as e:
            logger.error(f"Failed to record habit {habit_id} for user {user_id}: {e}")
            return False, "Error recording habit"

    # ========== SHEET 2: CONSUMPTION HABITS ==========
    
    def _ensure_consumption_sheet_structure(self):
        """Ensure Consumption sheet has proper structure"""
        try:
            if not self.consumption_sheet:
                return
            
            # Check if headers exist
            headers = self.consumption_sheet.row_values(1)
            expected_headers = [
                "User ID", "Date", "Week Number", "Coffee (x)", "Coffee Cost (руб)", 
                "Sugary (y)", "Sugary Cost (руб)", "Flour (z)", "Flour Cost (руб)"
            ]
            
            if headers != expected_headers:
                self.consumption_sheet.clear()
                self.consumption_sheet.append_row(expected_headers)
                logger.info("Consumption sheet structure initialized")
        except Exception as e:
            logger.error(f"Failed to ensure consumption sheet structure: {e}")

    def _get_consumption_row(self, user_id, week_number, date=None):
        """Get or create user's row for consumption tracking"""
        try:
            if not self.consumption_sheet:
                return None, None
            
            if date is None:
                date = self._get_moscow_now()
            
            today_str = date.strftime("%Y-%m-%d")
            all_rows = self.consumption_sheet.get_all_values()
            
            # Find existing row for this user, week, and specific date
            for row_idx, row in enumerate(all_rows[1:], start=2):  # Skip header
                if len(row) > 2:
                    # Check User ID (col 0), Date (col 1), and Week Number (col 2)
                    if row[0] == str(user_id) and row[1] == today_str and row[2] == week_number:
                        return row_idx, row
            
            # Create new row for today
            new_row = [str(user_id), today_str, week_number, "", "", "", "", "", ""]
            self.consumption_sheet.append_row(new_row)
            return self.consumption_sheet.row_count, new_row
        except Exception as e:
            logger.error(f"Failed to get consumption row: {e}")
            return None, None

    def _parse_consumption_input(self, text):
        """Parse consumption input like 'xxx', 'xx 150', 'y 75', etc."""
        text = text.strip().lower()
        
        # Match pattern: (x,y,z letters) optional space optional number
        match = re.match(r'^([xyz]+)(?:\s+(\d+))?$', text)
        if not match:
            return None, None
        
        letters = match.group(1)
        cost = match.group(2)
        
        # Determine type (x, y, or z)
        if 'x' in letters:
            habit_type = 'x'
        elif 'y' in letters:
            habit_type = 'y'
        elif 'z' in letters:
            habit_type = 'z'
        else:
            return None, None
        
        # Count the specific letters (filter only the relevant type)
        count = letters.count(habit_type)
        
        # Convert cost to integer if provided
        cost_int = int(cost) if cost else 0
        
        return habit_type, count, cost_int

    def _record_consumption(self, user_id, text):
        """Record consumption in Sheet2"""
        try:
            if not self.consumption_sheet:
                return False, "Consumption sheet not initialized"
            
            # Parse input
            result = self._parse_consumption_input(text)
            if not result:
                return False, "Invalid format. Use like 'x', 'xxx', 'xx 150', 'y 75', 'zzz 200'"
            
            habit_type, count, cost = result
            
            # Get current date and week
            now = self._get_moscow_now()
            today_str = now.strftime("%Y-%m-%d")
            week_number = self._get_week_number(now)
            
            # Get or create row for today
            row_num, row_data = self._get_consumption_row(user_id, week_number, now)
            if row_num is None:
                return False, "Failed to create consumption record"
            
            # Determine columns based on type
            if habit_type == 'x':
                count_col = 4  # Coffee (x)
                cost_col = 5   # Coffee Cost
            elif habit_type == 'y':
                count_col = 6  # Sugary (y)
                cost_col = 7   # Sugary Cost
            else:  # 'z'
                count_col = 8  # Flour (z)
                cost_col = 9   # Flour Cost
            
            # Get current values
            current_count_str = self.consumption_sheet.cell(row_num, count_col).value or "0"
            current_cost_str = self.consumption_sheet.cell(row_num, cost_col).value or "0"
            
            # Parse current values
            current_count = int(current_count_str) if current_count_str.isdigit() else 0
            current_cost = int(current_cost_str) if current_cost_str.isdigit() else 0
            
            # Update values
            new_count = current_count + count
            new_cost = current_cost + cost
            
            # Update cells
            self.consumption_sheet.update_cell(row_num, count_col, str(new_count))
            if cost > 0:
                self.consumption_sheet.update_cell(row_num, cost_col, str(new_cost))
            
            # Prepare response
            habit_name = CONSUMPTION_HABITS[habit_type]
            response = f"✓ {habit_name}: +{count} dose(s)"
            if cost > 0:
                response += f", +{cost} руб"
            response += f"\nToday's total: {new_count} dose(s)"
            if new_cost > 0:
                response += f", {new_cost} руб"
            
            logger.info(f"Recorded consumption: user={user_id}, type={habit_type}, count={count}, cost={cost}")
            return True, response
            
        except Exception as e:
            logger.error(f"Failed to record consumption: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, "Error recording consumption"

    def _get_weekly_consumption_summary(self, user_id):
        """Get weekly consumption summary for feedback"""
        try:
            if not self.consumption_sheet:
                return None
            
            week_number = self._get_week_number()
            all_rows = self.consumption_sheet.get_all_values()
            
            totals = {
                'x_count': 0,
                'x_cost': 0,
                'y_count': 0,
                'y_cost': 0,
                'z_count': 0,
                'z_cost': 0
            }
            
            for row in all_rows[1:]:
                if len(row) > 8 and row[0] == str(user_id) and row[2] == week_number:
                    # Coffee
                    if row[3] and row[3].isdigit():
                        totals['x_count'] += int(row[3])
                    if row[4] and row[4].isdigit():
                        totals['x_cost'] += int(row[4])
                    
                    # Sugary
                    if row[5] and row[5].isdigit():
                        totals['y_count'] += int(row[5])
                    if row[6] and row[6].isdigit():
                        totals['y_cost'] += int(row[6])
                    
                    # Flour
                    if row[7] and row[7].isdigit():
                        totals['z_count'] += int(row[7])
                    if row[8] and row[8].isdigit():
                        totals['z_cost'] += int(row[8])
            
            return totals
        except Exception as e:
            logger.error(f"Failed to get weekly consumption summary: {e}")
            return None

    def _format_consumption_feedback(self, totals):
        """Format consumption feedback for weekly report"""
        if not totals:
            return "No consumption data this week."
        
        feedback = "☕ **Consumption Summary**\n\n"
        
        # Coffee
        feedback += f"• Coffee (x): {totals['x_count']} dose(s)"
        if totals['x_cost'] > 0:
            feedback += f", {totals['x_cost']} руб"
        feedback += "\n"
        
        # Sugary
        feedback += f"• Sugary food (y): {totals['y_count']} dose(s)"
        if totals['y_cost'] > 0:
            feedback += f", {totals['y_cost']} руб"
        feedback += "\n"
        
        # Flour
        feedback += f"• Flour-based food (z): {totals['z_count']} dose(s)"
        if totals['z_cost'] > 0:
            feedback += f", {totals['z_cost']} руб"
        feedback += "\n"
        
        # Calculate totals
        total_cost = totals['x_cost'] + totals['y_cost'] + totals['z_cost']
        feedback += f"\n💰 **Weekly total spent**: {total_cost} руб"
        
        return feedback

    # ========== TELEGRAM HANDLERS ==========
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        await update.message.reply_text(
            "🥋 Welcome to Sambo Habits & Consumption Tracker!\n\n"
            "**For Sambo Habits (1-5):**\n"
            "1 - Prayer with first water\n"
            "2 - Qi Gong routine\n"
            "3 - Freestyling on the ball\n"
            "4 - 20 minute run and stretch\n"
            "5 - Strengthening and stretching\n\n"
            "**For Consumption Tracking:**\n"
            "• x - Coffee dose (x, xx, xxx 150)\n"
            "• y - Sugary food (y, yy 75)\n"
            "• z - Flour-based food (z, zz 200)\n\n"
            "Add price after space if purchased.\n"
            "Send each entry separately. Sunday is rest day."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Check for consumption entries first (x, y, z)
        if text and text[0].lower() in ['x', 'y', 'z']:
            success, message = self._record_consumption(user_id, text)
            await update.message.reply_text(message)
            return
        
        # Check for sambo habit numbers (1-5)
        if text.isdigit() and 1 <= int(text) <= 5:
            habit_id = int(text)
            success, message = self._record_habit(user_id, habit_id)
            await update.message.reply_text(message)
            return
        
        # Check for other consumption patterns
        if any(char.lower() in ['x', 'y', 'z'] for char in text):
            success, message = self._record_consumption(user_id, text)
            await update.message.reply_text(message)
            return
        
        # Unknown input
        await update.message.reply_text(
            "Please send:\n"
            "• A number 1-5 for Sambo habits\n"
            "• x, y, or z for consumption (e.g., 'x', 'xx 150', 'yyy 200')"
        )

    async def send_weekly_feedback(self, context: ContextTypes.DEFAULT_TYPE):
        """Send weekly feedback on Saturday at 18:20 Moscow time"""
        logger.info("Sending weekly feedback")
        
        try:
            # Get all users from both sheets
            sambo_users = set()
            consumption_users = set()
            
            # Get users from Sambo sheet
            if self.sheet:
                all_rows = self.sheet.get_all_values()
                for row in all_rows[1:]:
                    if row and row[0]:
                        try:
                            sambo_users.add(int(row[0]))
                        except ValueError:
                            continue
            
            # Get users from Consumption sheet
            if self.consumption_sheet:
                all_rows = self.consumption_sheet.get_all_values()
                for row in all_rows[1:]:
                    if row and row[0]:
                        try:
                            consumption_users.add(int(row[0]))
                        except ValueError:
                            continue
            
            # Combine all users
            all_users = sambo_users.union(consumption_users)
            
            for user_id in all_users:
                try:
                    # Send consumption summary
                    totals = self._get_weekly_consumption_summary(user_id)
                    if totals and (totals['x_count'] > 0 or totals['y_count'] > 0 or totals['z_count'] > 0):
                        consumption_feedback = self._format_consumption_feedback(totals)
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=consumption_feedback,
                            parse_mode="Markdown"
                        )
                        await asyncio.sleep(1)  # Small delay between messages
                        
                    # Note: You could add Sambo feedback here too if needed
                    # (you already have the logic from your original code)
                    
                except Exception as e:
                    logger.error(f"Failed to send feedback to user {user_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to send weekly feedback: {e}")
            import traceback
            logger.error(traceback.format_exc())

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
                # Consumption feedback at 18:20 on Saturday
                job_queue.run_daily(
                    self.send_weekly_feedback,
                    time=datetime.strptime("18:20", "%H:%M").time(),
                    days=[5],  # Saturday
                    tzinfo=MOSCOW_TZ
                )
                logger.info("Scheduled consumption feedback for Saturday 18:20 Moscow time")
        except Exception as e:
            logger.warning(f"Could not set up job queue: {e}")
        
        logger.info("Bot started and polling for messages...")
        app.run_polling()


if __name__ == "__main__":
    bot = SamboBot()
    bot.run()
