import logging
import os
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, ContextTypes
from telegram.ext import MessageHandler, filters
import psycopg
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import asyncio

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-domain.com')
PORT = int(os.getenv('PORT', 5000))

# Flask app for API
app = Flask(__name__)
CORS(app)

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg.connect(DATABASE_URL)
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def ensure_connection(self):
        """Ensure database connection is alive"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT 1')
        except:
            logger.warning("Database connection lost, reconnecting...")
            self.connect()
    
    def create_tables(self):
        """Create users table if not exists"""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    pigeon_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
        logger.info("Database tables created/verified")
    
    def get_user(self, user_id):
        """Get user data"""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            row = cur.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'pigeon_count': row[3],
                    'created_at': row[4]
                }
            return None
    
    def create_user(self, user_id, username, first_name):
        """Create new user"""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute(
                '''INSERT INTO users (user_id, username, first_name, pigeon_count) 
                   VALUES (%s, %s, %s, 0) 
                   ON CONFLICT (user_id) 
                   DO UPDATE SET username = %s, first_name = %s''',
                (user_id, username, first_name, username, first_name)
            )
            self.conn.commit()
    
    def add_pigeon(self, user_id):
        """Increment pigeon count for user"""
        self.ensure_connection()
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
    
    def get_total_users(self):
        """Get total number of users"""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM users')
            return cur.fetchone()[0]
    
    def get_total_pigeons(self):
        """Get total number of pigeons across all users"""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute('SELECT COALESCE(SUM(pigeon_count), 0) FROM users')
            result = cur.fetchone()[0]
            return result if result else 0

# Initialize database
db = Database()

# Flask API Endpoints
@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Pigeon Bot API is running'})

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """Get user statistics"""
    try:
        user = db.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        total_users = db.get_total_users()
        total_pigeons = db.get_total_pigeons()
        
        return jsonify({
            'name': user['first_name'],
            'username': user['username'] or 'N/A',
            'pigeons': user['pigeon_count'],
            'totalUsers': total_users,
            'totalPigeons': total_pigeons,
            'totalStars': total_pigeons * 1000
        })
    except Exception as e:
        logger.error(f"Error in get_user_stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_global_stats():
    """Get global statistics"""
    try:
        total_users = db.get_total_users()
        total_pigeons = db.get_total_pigeons()
        
        return jsonify({
            'totalUsers': total_users,
            'totalPigeons': total_pigeons,
            'totalStars': total_pigeons * 1000
        })
    except Exception as e:
        logger.error(f"Error in get_global_stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Bot Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - welcome message"""
    user = update.effective_user
    db.create_user(user.id, user.username, user.first_name)
    
    # Create inline keyboard with buy button and web app
    keyboard = [
        [InlineKeyboardButton("🕊️ اشتري حمامة (1000 نجمة)", callback_data='buy_pigeon')],
        [InlineKeyboardButton("📊 عرض الإحصائيات", 
                            web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user.id}"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"مرحباً {user.first_name}! 🕊️\n\n"
        f"اشترِ حمامة مقابل 1000 نجمة تلغرام!\n"
        f"حمامك الحالي: {db.get_pigeon_count(user.id)} 🕊️\n\n"
        f"استخدم الأزرار أدناه للشراء أو عرض الإحصائيات.",
        reply_markup=reply_markup
    )

async def my_pigeons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's pigeon count"""
    user = update.effective_user
    pigeon_count = db.get_pigeon_count(user.id)
    total_users = db.get_total_users()
    total_pigeons = db.get_total_pigeons()
    
    keyboard = [
        [InlineKeyboardButton("🕊️ اشتري المزيد", callback_data='buy_pigeon')],
        [InlineKeyboardButton("📊 عرض الإحصائيات", 
                            web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user.id}"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🕊️ حماماتك: {pigeon_count}\n\n"
        f"📊 الإحصائيات العامة:\n"
        f"👥 إجمالي المستخدمين: {total_users}\n"
        f"🌍 إجمالي الحمام: {total_pigeons}\n"
        f"⭐ نجوم محصلة: {total_pigeons * 1000}\n\n"
        f"المستخدم: @{user.username or 'N/A'}",
        reply_markup=reply_markup
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show global statistics"""
    total_users = db.get_total_users()
    total_pigeons = db.get_total_pigeons()
    user_pigeons = db.get_pigeon_count(update.effective_user.id)
    
    await update.message.reply_text(
        f"📊 إحصائيات بوت الحمام\n\n"
        f"🕊️ حماماتك: {user_pigeons}\n"
        f"👥 إجمالي المستخدمين: {total_users}\n"
        f"🌍 إجمالي الحمام: {total_pigeons}\n"
        f"⭐ نجوم محصلة: {total_pigeons * 1000}"
    )

async def buy_pigeon_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy pigeon button"""
    query = update.callback_query
    await query.answer()
    
    # Create invoice for 1000 stars
    title = "شراء حمامة"
    description = "اشترِ حمامة واحدة لمجموعتك"
    payload = "pigeon_purchase"
    currency = "XTR"  # Telegram Stars currency
    prices = [LabeledPrice("حمامة", 1000)]  # 1000 stars
    
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
    
    keyboard = [
        [InlineKeyboardButton("🕊️ اشتري حمامة أخرى", callback_data='buy_pigeon')],
        [InlineKeyboardButton("📊 عرض الإحصائيات", 
                            web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user.id}"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎉 مبروك! اشتريت حمامة!\n\n"
        f"إجمالي حماماتك: {pigeon_count} 🕊️",
        reply_markup=reply_markup
    )

def run_flask():
    """Run Flask API server"""
    app.run(host='0.0.0.0', port=5000)

def main():
    """Start the bot"""
    # Start Flask API in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Build telegram bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mypigeons", my_pigeons))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(buy_pigeon_callback, pattern='buy_pigeon'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # Run the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
