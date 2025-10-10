import logging
import os
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, ContextTypes
import psycopg

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

class Database:
    def __init__(self):
        self.conn = psycopg.connect(DATABASE_URL)
        self.create_tables()
    
    def create_tables(self):
        """Create users table if not exists"""
        with self.conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    pigeon_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
    
    def get_user(self, user_id):
        """Get user data"""
        with self.conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            row = cur.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'pigeon_count': row[2],
                    'created_at': row[3]
                }
            return None
    
    def create_user(self, user_id, username):
        """Create new user"""
        with self.conn.cursor() as cur:
            cur.execute(
                'INSERT INTO users (user_id, username, pigeon_count) VALUES (%s, %s, 0) ON CONFLICT (user_id) DO NOTHING',
                (user_id, username)
            )
            self.conn.commit()
    
    def add_pigeon(self, user_id):
        """Increment pigeon count for user"""
        with self.conn.cursor() as cur:
            cur.execute(
                'UPDATE users SET pigeon_count = pigeon_count + 1 WHERE user_id = %s',
                (user_id,)
            )
            self.conn.commit()
    
    def get_pigeon_count(self, user_id):
        """Get user's pigeon count"""
        user = self.get_user(user_id)
        return user['pigeon_count'] if user else 0

# Initialize database
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - welcome message"""
    user = update.effective_user
    db.create_user(user.id, user.username)
    
    keyboard = [[InlineKeyboardButton("🕊️ Buy Pigeon (1000 Stars)", callback_data='buy_pigeon')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Welcome {user.first_name}! 🕊️\n\n"
        f"Buy a pigeon for 1000 Telegram Stars!\n"
        f"Your current pigeons: {db.get_pigeon_count(user.id)}",
        reply_markup=reply_markup
    )

async def my_pigeons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's pigeon count"""
    user = update.effective_user
    pigeon_count = db.get_pigeon_count(user.id)
    
    await update.message.reply_text(
        f"🕊️ Your Pigeons: {pigeon_count}\n\n"
        f"Username: @{user.username or 'N/A'}"
    )

async def buy_pigeon_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy pigeon button"""
    query = update.callback_query
    await query.answer()
    
    # Create invoice for 1000 stars
    title = "Buy a Pigeon"
    description = "Purchase one pigeon for your collection"
    payload = "pigeon_purchase"
    currency = "XTR"  # Telegram Stars currency
    prices = [LabeledPrice("Pigeon", 1000)]  # 1000 stars
    
    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Empty for Telegram Stars
        currency=currency,
        prices=prices
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pre-checkout query"""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment"""
    user = update.effective_user
    
    # Add pigeon to user's account
    db.add_pigeon(user.id)
    pigeon_count = db.get_pigeon_count(user.id)
    
    keyboard = [[InlineKeyboardButton("🕊️ Buy Another Pigeon", callback_data='buy_pigeon')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎉 Congratulations! You bought a pigeon!\n\n"
        f"Your total pigeons: {pigeon_count} 🕊️",
        reply_markup=reply_markup
    )

def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mypigeons", my_pigeons))
    application.add_handler(CallbackQueryHandler(buy_pigeon_callback, pattern='buy_pigeon'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
