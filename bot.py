"""
Sambo Habits Tracking Telegram Bot
Tracks activity, consumption, and language learning habits with Google Sheets integration
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

# Sheet 1: Sambo Activity Habits
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

# Sheet 3: Language Learning Habits
LANGUAGE_HABITS = {
    'ch': "Chinese activation",
    'he': "Hebrew cards",
    'ta': "Tatar cards"
}

class SamboBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        # Initialize Google Sheets
        self.gs_client = None
        self.activity_sheet = None
        self.consumption_sheet = None
        self.language_sheet = None
        self._init_google_sheets()
        
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
            
            # Get or create the three sheets
            try:
                self.activity_sheet = spreadsheet.worksheet("Activity")
            except gspread.WorksheetNotFound:
                self.activity_sheet = spreadsheet.add_worksheet(title="Activity", rows=100, cols=10)
                logger.info("Created Activity sheet")
            
            try:
                self.consumption_sheet = spreadsheet.worksheet("Consumption")
            except gspread.WorksheetNotFound:
                self.consumption_sheet = spreadsheet.add_worksheet(title="Consumption", rows=100, cols=10)
                logger.info("Created Consumption sheet")
            
            try:
                self.language_sheet = spreadsheet.worksheet("Language")
            except gspread.WorksheetNotFound:
                self.language_sheet = spreadsheet.add_worksheet(title="Language", rows=100, cols=10)
                logger.info("Created Language sheet")
            
            # Initialize sheet structures
            self._ensure_activity_sheet_structure()
            self._ensure_consumption_sheet_structure()
            self._ensure_language_sheet_structure()
            
            logger.info("Google Sheets initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _trim_sheet(self, worksheet):
        """Remove empty rows and columns beyond actual data to prevent phantom cells"""
        try:
            # Just ensure minimum size, don't trim down
            current_rows = worksheet.row_count
            current_cols = worksheet.col_count
            
            min_rows = 200
            min_cols = 15
            
            if current_rows < min_rows or current_cols < min_cols:
                worksheet.resize(rows=max(current_rows, min_rows), cols=max(current_cols, min_cols))
                logger.info(f"Resized sheet {worksheet.title} to {max(current_rows, min_rows)}x{max(current_cols, min_cols)}")
                
        except Exception as e:
            logger.error(f"Failed to resize sheet: {e}")

    def _get_moscow_now(self):
        """Get current time in Moscow timezone"""
        return datetime.now(MOSCOW_TZ)

    def _get_week_start(self, date=None):
        """Get Monday of the current week"""
        if date is None:
            date = self._get_moscow_now()
        
        days_since_monday = date.weekday()
        week_start = date - timedelta(days=days_since_monday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    def _get_week_number(self, date=None):
        """Get week number for tracking"""
        if date is None:
            date = self._get_moscow_now()
        week_start = self._get_week_start(date)
        return week_start.strftime("%Y-%m-%d")

    # ========== SHEET 1: ACTIVITY HABITS ==========
    
    def _ensure_activity_sheet_structure(self):
        """Ensure Activity sheet has proper structure"""
        try:
            if not self.activity_sheet:
                return
            
            headers = self.activity_sheet.row_values(1) if self.activity_sheet.row_count > 0 else []
            expected_headers = [
                "User ID", "Date", "Prayer", "Qi Gong", "Ball", "Run/Stretch", 
                "Strength/Stretch", "Week Number", "Goals"
            ]
            
            if headers != expected_headers:
                self.activity_sheet.clear()
                self.activity_sheet.append_row(expected_headers)
                logger.info("Activity sheet structure initialized")
                
            self._trim_sheet(self.activity_sheet)
        except Exception as e:
            logger.error(f"Failed to ensure activity sheet structure: {e}")

    def _get_activity_row(self, user_id, date=None):
        """Get or create user's row for the day in Activity sheet"""
        try:
            if date is None:
                date = self._get_moscow_now()
            
            today_str = date.strftime("%Y-%m-%d")
            week_number = self._get_week_number(date)
            
            all_rows = self.activity_sheet.get_all_values()
            logger.info(f"Activity sheet has {len(all_rows)} rows total")
            
            # Look for existing row for this user and date
            for row_idx, row in enumerate(all_rows[1:], start=2):
                if len(row) > 1:
                    if row[0] == str(user_id) and row[1] == today_str:
                        logger.info(f"Found existing row {row_idx} for user {user_id} on {today_str}")
                        return row_idx, row
            
            # Create new row for today
            new_row = [str(user_id), today_str, "", "", "", "", "", week_number, ""]
            self.activity_sheet.append_row(new_row)
            new_row_num = len(all_rows) + 1
            logger.info(f"Created new row {new_row_num} for user {user_id} on {today_str}")
            return new_row_num, new_row
        except Exception as e:
            logger.error(f"Failed to get activity row: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None

    def _record_habit(self, user_id, habit_id):
        """Record a completed habit in Activity sheet"""
        try:
            if not self.activity_sheet:
                return False, "Activity sheet not initialized"
            
            if habit_id not in HABITS:
                return False, f"Invalid habit number. Use 1-5."
            
            row_num, row_data = self._get_activity_row(user_id)
            
            if row_num is None:
                return False, "Failed to record habit"
            
            # Column mapping: 1->C(3), 2->D(4), 3->E(5), 4->F(6), 5->G(7)
            col_map = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7}
            col = col_map[habit_id]
            
            # Check if already recorded
            current_value = self.activity_sheet.cell(row_num, col).value
            
            if current_value and current_value.strip():
                return False, f"{HABITS[habit_id]} already recorded today"
            
            # Record the habit
            self.activity_sheet.update_cell(row_num, col, "✓")
            
            logger.info(f"Recorded habit {habit_id} for user {user_id}")
            return True, f"✓ {HABITS[habit_id]} recorded!"
        except Exception as e:
            logger.error(f"Failed to record habit: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, "Error recording habit"

    # ========== SHEET 2: CONSUMPTION HABITS ==========
    
    def _ensure_consumption_sheet_structure(self):
        """Ensure Consumption sheet has proper structure"""
        try:
            if not self.consumption_sheet:
                return
            
            headers = self.consumption_sheet.row_values(1) if self.consumption_sheet.row_count > 0 else []
            expected_headers = [
                "User ID", "Date", "Week Number", "Coffee (x)", "Coffee Cost", 
                "Sugary (y)", "Sugary Cost", "Flour (z)", "Flour Cost"
            ]
            
            if headers != expected_headers:
                self.consumption_sheet.clear()
                self.consumption_sheet.append_row(expected_headers)
                logger.info("Consumption sheet structure initialized")
                
            self._trim_sheet(self.consumption_sheet)
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
            logger.info(f"Consumption sheet has {len(all_rows)} rows total")
            
            for row_idx, row in enumerate(all_rows[1:], start=2):
                if len(row) > 2:
                    if row[0] == str(user_id) and row[1] == today_str and row[2] == week_number:
                        logger.info(f"Found existing consumption row {row_idx}")
                        return row_idx, row
            
            # Create new row
            new_row = [str(user_id), today_str, week_number, "", "", "", "", "", ""]
            self.consumption_sheet.append_row(new_row)
            new_row_num = len(all_rows) + 1
            logger.info(f"Created new consumption row {new_row_num}")
            return new_row_num, new_row
        except Exception as e:
            logger.error(f"Failed to get consumption row: {e}")
            return None, None

    def _parse_consumption_input(self, text):
        """Parse consumption input like 'xxx', 'xx 150', 'y 75', etc."""
        text = text.strip().lower()
        
        match = re.match(r'^([xyz]+)(?:\s+(\d+))?$', text)
        if not match:
            return None
        
        letters = match.group(1)
        cost = match.group(2)
        
        if 'x' in letters:
            habit_type = 'x'
        elif 'y' in letters:
            habit_type = 'y'
        elif 'z' in letters:
            habit_type = 'z'
        else:
            return None
        
        count = letters.count(habit_type)
        cost_int = int(cost) if cost else 0
        
        return habit_type, count, cost_int

    def _record_consumption(self, user_id, text):
        """Record consumption in Consumption sheet"""
        try:
            if not self.consumption_sheet:
                return False, "Consumption sheet not initialized"
            
            result = self._parse_consumption_input(text)
            if not result:
                return False, "Invalid format. Use: 'x', 'xxx', 'xx 150', 'y 75', 'zzz 200'"
            
            habit_type, count, cost = result
            
            now = self._get_moscow_now()
            week_number = self._get_week_number(now)
            
            row_num, row_data = self._get_consumption_row(user_id, week_number, now)
            if row_num is None:
                return False, "Failed to create consumption record"
            
            if habit_type == 'x':
                count_col, cost_col = 4, 5
            elif habit_type == 'y':
                count_col, cost_col = 6, 7
            else:
                count_col, cost_col = 8, 9
            
            current_count_str = self.consumption_sheet.cell(row_num, count_col).value or "0"
            current_cost_str = self.consumption_sheet.cell(row_num, cost_col).value or "0"
            
            current_count = int(current_count_str) if current_count_str.isdigit() else 0
            current_cost = int(current_cost_str) if current_cost_str.isdigit() else 0
            
            new_count = current_count + count
            new_cost = current_cost + cost
            
            self.consumption_sheet.update_cell(row_num, count_col, str(new_count))
            if cost > 0:
                self.consumption_sheet.update_cell(row_num, cost_col, str(new_cost))
            
            habit_name = CONSUMPTION_HABITS[habit_type]
            response = f"✓ {habit_name}: +{count} dose(s)"
            if cost > 0:
                response += f", +{cost} руб"
            response += f"\nToday's total: {new_count} dose(s)"
            if new_cost > 0:
                response += f", {new_cost} руб"
            
            logger.info(f"Recorded consumption: type={habit_type}, count={count}, cost={cost}")
            return True, response
            
        except Exception as e:
            logger.error(f"Failed to record consumption: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, "Error recording consumption"

    # ========== SHEET 3: LANGUAGE LEARNING HABITS ==========
    
    def _ensure_language_sheet_structure(self):
        """Ensure Language sheet has proper structure"""
        try:
            if not self.language_sheet:
                return
            
            headers = self.language_sheet.row_values(1) if self.language_sheet.row_count > 0 else []
            expected_headers = [
                "User ID", "Date", "Week Number", "Chinese (ch)", "Hebrew (he)", "Tatar (ta)"
            ]
            
            if headers != expected_headers:
                self.language_sheet.clear()
                self.language_sheet.append_row(expected_headers)
                logger.info("Language sheet structure initialized")
                
            self._trim_sheet(self.language_sheet)
        except Exception as e:
            logger.error(f"Failed to ensure language sheet structure: {e}")

    def _get_language_row(self, user_id, week_number, date=None):
        """Get or create user's row for language tracking"""
        try:
            if not self.language_sheet:
                return None, None
            
            if date is None:
                date = self._get_moscow_now()
            
            today_str = date.strftime("%Y-%m-%d")
            all_rows = self.language_sheet.get_all_values()
            logger.info(f"Language sheet has {len(all_rows)} rows total")
            
            for row_idx, row in enumerate(all_rows[1:], start=2):
                if len(row) > 2:
                    if row[0] == str(user_id) and row[1] == today_str and row[2] == week_number:
                        logger.info(f"Found existing language row {row_idx}")
                        return row_idx, row
            
            # Create new row
            new_row = [str(user_id), today_str, week_number, "", "", ""]
            self.language_sheet.append_row(new_row)
            new_row_num = len(all_rows) + 1
            logger.info(f"Created new language row {new_row_num}")
            return new_row_num, new_row
        except Exception as e:
            logger.error(f"Failed to get language row: {e}")
            return None, None

    def _record_language(self, user_id, text):
        """Record language learning activity"""
        try:
            if not self.language_sheet:
                return False, "Language sheet not initialized"
            
            text = text.strip().lower()
            
            # Determine language type
            if text == 'ch':
                lang_type = 'ch'
                col = 4
            elif text == 'he':
                lang_type = 'he'
                col = 5
            elif text == 'ta':
                lang_type = 'ta'
                col = 6
            else:
                return False, "Invalid language code. Use: 'ch', 'he', or 'ta'"
            
            now = self._get_moscow_now()
            week_number = self._get_week_number(now)
            
            row_num, row_data = self._get_language_row(user_id, week_number, now)
            if row_num is None:
                return False, "Failed to create language record"
            
            # Check if already recorded today
            current_value = self.language_sheet.cell(row_num, col).value
            if current_value:
                return False, f"{LANGUAGE_HABITS[lang_type]} already recorded today"
            
            # Record the activity
            self.language_sheet.update_cell(row_num, col, "✓")
            
            habit_name = LANGUAGE_HABITS[lang_type]
            logger.info(f"Recorded language activity: type={lang_type}")
            return True, f"✓ {habit_name} recorded!"
            
        except Exception as e:
            logger.error(f"Failed to record language activity: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, "Error recording language activity"

    def _get_weekly_language_summary(self, user_id):
        """Get weekly language learning summary"""
        try:
            if not self.language_sheet:
                return None
            
            week_number = self._get_week_number()
            all_rows = self.language_sheet.get_all_values()
            
            totals = {'ch': 0, 'he': 0, 'ta': 0}
            
            for row in all_rows[1:]:
                if len(row) > 5 and row[0] == str(user_id) and row[2] == week_number:
                    if row[3] == "✓":
                        totals['ch'] += 1
                    if row[4] == "✓":
                        totals['he'] += 1
                    if row[5] == "✓":
                        totals['ta'] += 1
            
            return totals
        except Exception as e:
            logger.error(f"Failed to get weekly language summary: {e}")
            return None

    # ========== TELEGRAM HANDLERS ==========
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        await update.message.reply_text(
            "🥋 Welcome to Sambo Habits Tracker!\n\n"
            "**Activity Habits (1-5):**\n"
            "1 - Prayer with first water\n"
            "2 - Qi Gong routine\n"
            "3 - Freestyling on the ball\n"
            "4 - 20 minute run and stretch\n"
            "5 - Strengthening and stretching\n\n"
            "**Consumption Tracking:**\n"
            "• x - Coffee (x, xx, xxx 150)\n"
            "• y - Sugary food (y, yy 75)\n"
            "• z - Flour food (z, zz 200)\n\n"
            "**Language Learning:**\n"
            "• ch - Chinese activation\n"
            "• he - Hebrew cards\n"
            "• ta - Tatar cards\n\n"
            "Send each entry separately. Sunday is rest day."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        user_id = update.effective_user.id
        text = update.message.text.strip().lower()
        
        # Check for language learning (ch, he, ta)
        if text in ['ch', 'he', 'ta']:
            success, message = self._record_language(user_id, text)
            await update.message.reply_text(message)
            return
        
        # Check for consumption entries (x, y, z)
        if text and text[0] in ['x', 'y', 'z']:
            success, message = self._record_consumption(user_id, text)
            await update.message.reply_text(message)
            return
        
        # Check for activity habit numbers (1-5)
        if text.isdigit() and 1 <= int(text) <= 5:
            habit_id = int(text)
            success, message = self._record_habit(user_id, habit_id)
            await update.message.reply_text(message)
            return
        
        # Unknown input
        await update.message.reply_text(
            "Please send:\n"
            "• 1-5 for activity habits\n"
            "• x/y/z for consumption (e.g., 'x', 'xx 150')\n"
            "• ch/he/ta for language learning"
        )

    def run(self):
        """Start the bot"""
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            return
        
        app = Application.builder().token(self.bot_token).build()
        
        # Handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Bot started and polling for messages...")
        app.run_polling()


if __name__ == "__main__":
    bot = SamboBot()
    bot.run()
