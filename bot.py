"""
Telegram Bot - Sell Python Codes for Stars
Enhanced version with PostgreSQL Database
"""

import requests
import time
import json
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================
# Configuration
# ============================================
BOT_TOKEN = "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
PRICE_PER_CODE = 999

# Database connection from Railway environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# ============================================
# Database Functions
# ============================================

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create purchases table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                code_id VARCHAR(10),
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                price INTEGER,
                UNIQUE(user_id, code_id)
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        if conn:
            conn.close()
        return False


def save_user(user_id, username, first_name, last_name):
    """Save or update user information"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Insert or update user
        cur.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, join_date, last_activity)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                last_activity = EXCLUDED.last_activity
        """, (user_id, username, first_name, last_name, datetime.now(), datetime.now()))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error saving user: {e}")
        if conn:
            conn.close()
        return False


def get_user(user_id):
    """Get user information"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        if conn:
            conn.close()
        return None


def save_purchase(user_id, code_id, price):
    """Save purchase"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO purchases (user_id, code_id, price)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, code_id) DO NOTHING
        """, (user_id, code_id, price))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error saving purchase: {e}")
        if conn:
            conn.close()
        return False


def get_user_purchases(user_id):
    """Get all purchases for a user"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM purchases WHERE user_id = %s", (user_id,))
        purchases = cur.fetchall()
        cur.close()
        conn.close()
        return [p['code_id'] for p in purchases]
    except Exception as e:
        print(f"❌ Error getting purchases: {e}")
        if conn:
            conn.close()
        return []


def check_purchase(user_id, code_id):
    """Check if user purchased a code"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM purchases 
            WHERE user_id = %s AND code_id = %s
        """, (user_id, code_id))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"❌ Error checking purchase: {e}")
        if conn:
            conn.close()
        return False


def get_all_users():
    """Get all users (for admin)"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users ORDER BY join_date DESC")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return users
    except Exception as e:
        print(f"❌ Error getting all users: {e}")
        if conn:
            conn.close()
        return []


def get_stats():
    """Get bot statistics"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        
        # Total users
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        
        # Total purchases
        cur.execute("SELECT COUNT(*) FROM purchases")
        total_purchases = cur.fetchone()[0]
        
        # Total revenue
        cur.execute("SELECT SUM(price) FROM purchases")
        total_revenue = cur.fetchone()[0] or 0
        
        cur.close()
        conn.close()
        
        return {
            "total_users": total_users,
            "total_purchases": total_purchases,
            "total_revenue": total_revenue
        }
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        if conn:
            conn.close()
        return None

# ============================================
# Python Codes Collection
# ============================================
CODES = {
    "1": {
        "name": "🌡️ Temperature Converter",
        "desc": "Convert between Celsius and Fahrenheit",
        "emoji": "🌡️",
        "code": """def celsius_to_fahrenheit(c):
    return (c * 9/5) + 32

def fahrenheit_to_celsius(f):
    return (f - 32) * 5/9

print(f"25°C = {celsius_to_fahrenheit(25)}°F")
print(f"77°F = {fahrenheit_to_celsius(77)}°C")"""
    },
    "2": {
        "name": "🔐 Password Generator",
        "desc": "Generate secure random passwords",
        "emoji": "🔐",
        "code": """import random
import string

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%"
    password = ''.join(random.choice(chars) for i in range(length))
    return password

print(generate_password(16))"""
    },
    "3": {
        "name": "📁 File Lister",
        "desc": "List all files in a directory",
        "emoji": "📁",
        "code": """import os

def list_files(path='.'):
    files = []
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            files.append(item)
    return files

for file in list_files():
    print(file)"""
    },
    "4": {
        "name": "📝 Word Counter",
        "desc": "Count words in any text",
        "emoji": "📝",
        "code": """def count_words(text):
    words = text.split()
    return len(words)

text = "Hello world from Python programming"
print(f"Total words: {count_words(text)}")"""
    },
    "5": {
        "name": "➕ List Summer",
        "desc": "Calculate sum of numbers",
        "emoji": "➕",
        "code": """def sum_numbers(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

my_list = [10, 20, 30, 40, 50]
print(f"Sum: {sum_numbers(my_list)}")"""
    },
    "6": {
        "name": "🔢 Max Finder",
        "desc": "Find maximum in a list",
        "emoji": "🔢",
        "code": """def find_max(numbers):
    if not numbers:
        return None
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num

numbers = [45, 23, 89, 12, 67]
print(f"Maximum: {find_max(numbers)}")"""
    },
    "7": {
        "name": "🔄 String Reverser",
        "desc": "Reverse any string",
        "emoji": "🔄",
        "code": """def reverse_string(text):
    return text[::-1]

original = "Python Programming"
reversed_text = reverse_string(original)
print(f"Original: {original}")
print(f"Reversed: {reversed_text}")"""
    },
    "8": {
        "name": "🎯 Even Checker",
        "desc": "Check if number is even or odd",
        "emoji": "🎯",
        "code": """def is_even(number):
    return number % 2 == 0

for i in range(1, 11):
    result = "Even" if is_even(i) else "Odd"
    print(f"{i} is {result}")"""
    },
    "9": {
        "name": "🧹 Duplicate Remover",
        "desc": "Remove duplicates from list",
        "emoji": "🧹",
        "code": """def remove_duplicates(items):
    return list(set(items))

my_list = [1, 2, 2, 3, 3, 4, 5, 5, 6]
clean_list = remove_duplicates(my_list)
print(f"Original: {my_list}")
print(f"Cleaned: {clean_list}")"""
    },
    "10": {
        "name": "🔤 Vowel Counter",
        "desc": "Count vowels in text",
        "emoji": "🔤",
        "code": """def count_vowels(text):
    vowels = 'aeiouAEIOU'
    count = 0
    for char in text:
        if char in vowels:
            count += 1
    return count

text = "Hello World Python"
print(f"Vowels in '{text}': {count_vowels(text)}")"""
    }
}

# ============================================
# Storage
# ============================================
last_update_id = 0

# ============================================
# Helper Functions
# ============================================

def send_message(chat_id, text, reply_markup=None):
    """Send message with optional keyboard"""
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    """Edit existing message"""
    url = f"{BASE_URL}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ Error editing message: {e}")
        return None


def answer_callback(callback_id, text=""):
    """Answer callback query"""
    url = f"{BASE_URL}/answerCallbackQuery"
    data = {
        "callback_query_id": callback_id,
        "text": text
    }
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass


def send_invoice(chat_id, code_id):
    """Send payment invoice"""
    code = CODES[code_id]
    url = f"{BASE_URL}/sendInvoice"
    
    payload = {
        "chat_id": chat_id,
        "title": code["name"],
        "description": code["desc"],
        "payload": f"code_{code_id}_{chat_id}",
        "currency": "XTR",
        "prices": [{"label": code["name"], "amount": PRICE_PER_CODE}]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ Error sending invoice: {e}")
        return None


def answer_pre_checkout(pre_checkout_id, ok=True):
    """Answer pre-checkout query"""
    url = f"{BASE_URL}/answerPreCheckoutQuery"
    data = {
        "pre_checkout_query_id": pre_checkout_id,
        "ok": ok
    }
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass


def extract_user_info(user_data):
    """Extract user information from message"""
    user_id = user_data.get("id")
    username = user_data.get("username", "")
    first_name = user_data.get("first_name", "")
    last_name = user_data.get("last_name", "")
    
    return user_id, username, first_name, last_name

# ============================================
# Command Handlers
# ============================================

def handle_start(chat_id, user_data):
    """Handle /start command"""
    # Save user info
    user_id, username, first_name, last_name = extract_user_info(user_data)
    save_user(user_id, username, first_name, last_name)
    
    # Get user info from database
    user = get_user(user_id)
    
    text = f"""
🎉 *مرحباً بك في متجر أكواد Python!*

👤 *معلوماتك:*
• الاسم: {first_name} {last_name}
• المعرف: @{username if username else 'غير متوفر'}
• تاريخ الانضمام: {user['join_date'].strftime('%Y-%m-%d %H:%M') if user else 'الآن'}

اشترِ أكواد برمجية بسيطة ومفيدة مقابل *999 نجمة تيليجرام* ⭐ لكل كود!

🛍️ *استخدم الأوامر التالية:*
/catalog - عرض جميع الأكواد
/mycodes - أكوادك المشتراة
/help - المساعدة

👇 *اضغط على الزر أدناه لبدء التسوق!*
"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🛍️ عرض الأكواد المتاحة", "callback_data": "show_catalog"}],
            [{"text": "📚 أكوادي", "callback_data": "my_codes"}]
        ]
    }
    
    send_message(chat_id, text, keyboard)


def handle_catalog(chat_id, message_id=None):
    """Show catalog with inline buttons"""
    text = "🛍️ *اختر الكود الذي تريد شراءه:*\n\n💰 السعر: *999 نجمة* ⭐ لكل كود\n"
    
    # Create inline keyboard with all codes
    keyboard = {"inline_keyboard": []}
    
    for code_id, code in CODES.items():
        button = {
            "text": f"{code['emoji']} {code['name']} - 999⭐",
            "callback_data": f"view_{code_id}"
        }
        keyboard["inline_keyboard"].append([button])
    
    # Add back button
    keyboard["inline_keyboard"].append([{"text": "🔙 رجوع", "callback_data": "back_to_start"}])
    
    if message_id:
        edit_message(chat_id, message_id, text, keyboard)
    else:
        send_message(chat_id, text, keyboard)


def handle_view_code(chat_id, message_id, code_id):
    """Show code details"""
    if code_id not in CODES:
        return
    
    code = CODES[code_id]
    owned = check_purchase(chat_id, code_id)
    
    text = f"""
{code['emoji']} *{code['name']}*

📝 *الوصف:*
{code['desc']}

💰 *السعر:* 999 نجمة ⭐
"""
    
    if owned:
        text += "\n✅ *أنت تملك هذا الكود بالفعل!*"
    
    # Create keyboard
    keyboard = {"inline_keyboard": []}
    
    if owned:
        keyboard["inline_keyboard"].append([
            {"text": "📥 عرض الكود", "callback_data": f"show_{code_id}"}
        ])
    else:
        keyboard["inline_keyboard"].append([
            {"text": f"💳 شراء مقابل 999⭐", "callback_data": f"buy_{code_id}"}
        ])
    
    keyboard["inline_keyboard"].append([
        {"text": "🔙 رجوع للكتالوج", "callback_data": "show_catalog"}
    ])
    
    edit_message(chat_id, message_id, text, keyboard)


def handle_buy(chat_id, code_id, callback_id):
    """Handle buy request"""
    if code_id not in CODES:
        answer_callback(callback_id, "❌ كود غير صالح")
        return
    
    # Check if already purchased
    if check_purchase(chat_id, code_id):
        answer_callback(callback_id, "✅ أنت تملك هذا الكود بالفعل!")
        return
    
    # Send invoice
    result = send_invoice(chat_id, code_id)
    
    if result and result.get("ok"):
        answer_callback(callback_id, "💳 جارِ إرسال فاتورة الدفع...")
    else:
        answer_callback(callback_id, "❌ حدث خطأ، حاول مرة أخرى")


def handle_show_code(chat_id, code_id):
    """Send code to user"""
    if not check_purchase(chat_id, code_id):
        send_message(chat_id, "❌ أنت لا تملك هذا الكود!")
        return
    
    code = CODES[code_id]
    text = f"""
{code['emoji']} *{code['name']}*

✅ *إليك الكود الخاص بك:*

```python
{code['code']}
```

💡 *نصيحة:* انسخ الكود واستخدمه في مشاريعك!
"""
    send_message(chat_id, text)


def handle_mycodes(chat_id, message_id=None):
    """Show user's purchased codes"""
    purchased_codes = get_user_purchases(chat_id)
    
    if not purchased_codes:
        text = "📭 *ليس لديك أي أكواد محفوظة بعد.*\n\nاضغط على الزر أدناه لشراء أكواد جديدة!"
        keyboard = {
            "inline_keyboard": [
                [{"text": "🛍️ عرض الأكواد المتاحة", "callback_data": "show_catalog"}],
                [{"text": "🔙 رجوع", "callback_data": "back_to_start"}]
            ]
        }
    else:
        text = "📚 *أكوادك المشتراة:*\n\n"
        
        keyboard = {"inline_keyboard": []}
        
        for code_id in purchased_codes:
            if code_id in CODES:
                code = CODES[code_id]
                text += f"✅ {code['emoji']} {code['name']}\n"
                
                button = {
                    "text": f"📥 {code['emoji']} {code['name']}",
                    "callback_data": f"show_{code_id}"
                }
                keyboard["inline_keyboard"].append([button])
        
        text += f"\n💰 *إجمالي الأكواد:* {len(purchased_codes)}"
        
        keyboard["inline_keyboard"].append([
            {"text": "🛍️ شراء المزيد", "callback_data": "show_catalog"},
            {"text": "🔙 رجوع", "callback_data": "back_to_start"}
        ])
    
    if message_id:
        edit_message(chat_id, message_id, text, keyboard)
    else:
        send_message(chat_id, text, keyboard)


def handle_successful_payment(chat_id, payload, user_data):
    """Handle successful payment"""
    parts = payload.split("_")
    code_id = parts[1]
    
    # Save purchase
    save_purchase(chat_id, code_id, PRICE_PER_CODE)
    
    # Update user activity
    user_id, username, first_name, last_name = extract_user_info(user_data)
    save_user(user_id, username, first_name, last_name)
    
    # Send success message
    code = CODES[code_id]
    text = f"""
🎉 *تم الدفع بنجاح!*

شكراً لشرائك! ✨

{code['emoji']} *{code['name']}*

إليك الكود الخاص بك:

```python
{code['code']}
```

💡 استخدم /mycodes لعرض جميع أكوادك
🛍️ استخدم /catalog لشراء المزيد!
"""
    send_message(chat_id, text)


def handle_stats(chat_id):
    """Show statistics (admin only)"""
    stats = get_stats()
    
    if not stats:
        send_message(chat_id, "❌ حدث خطأ في جلب الإحصائيات")
        return
    
    text = f"""
📊 *إحصائيات البوت*

👥 *عدد المستخدمين:* {stats['total_users']}
🛒 *عدد المشتريات:* {stats['total_purchases']}
💰 *إجمالي الإيرادات:* {stats['total_revenue']} ⭐

📅 *تاريخ اليوم:* {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    send_message(chat_id, text)

# ============================================
# Update Processing
# ============================================

def process_update(update):
    """Process incoming update"""
    
    # Handle callback queries (button clicks)
    if "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        message_id = query["message"]["message_id"]
        callback_id = query["id"]
        data = query["data"]
        user_data = query["from"]
        
        # Update user activity
        user_id, username, first_name, last_name = extract_user_info(user_data)
        save_user(user_id, username, first_name, last_name)
        
        answer_callback(callback_id)
        
        if data == "show_catalog":
            handle_catalog(chat_id, message_id)
        
        elif data == "my_codes":
            handle_mycodes(chat_id, message_id)
        
        elif data == "back_to_start":
            handle_start(chat_id, user_data)
        
        elif data.startswith("view_"):
            code_id = data.split("_")[1]
            handle_view_code(chat_id, message_id, code_id)
        
        elif data.startswith("buy_"):
            code_id = data.split("_")[1]
            handle_buy(chat_id, code_id, callback_id)
        
        elif data.startswith("show_"):
            code_id = data.split("_")[1]
            handle_show_code(chat_id, code_id)
        
        return
    
    # Handle messages
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_data = message["from"]
        
        # Handle successful payment
        if "successful_payment" in message:
            payload = message["successful_payment"]["invoice_payload"]
            handle_successful_payment(chat_id, payload, user_data)
            return
        
        # Handle text commands
        if "text" in message:
            text = message["text"]
            
            if text == "/start":
                handle_start(chat_id, user_data)
            
            elif text == "/catalog":
                handle_catalog(chat_id)
            
            elif text == "/mycodes":
                handle_mycodes(chat_id)
            
            elif text == "/stats":
                handle_stats(chat_id)
            
            elif text == "/help":
                handle_start(chat_id, user_data)
    
    # Handle pre-checkout query
    elif "pre_checkout_query" in update:
        query = update["pre_checkout_query"]
        answer_pre_checkout(query["id"], ok=True)


def get_updates():
    """Get updates from Telegram"""
    global last_update_id
    
    url = f"{BASE_URL}/getUpdates"
    params = {
        "offset": last_update_id + 1,
        "timeout": 30
    }
    
    try:
        response = requests.get(url, params=params, timeout=35)
        data = response.json()
        
        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                last_update_id = update["update_id"]
                process_update(update)
        
        return True
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return False

# ============================================
# Main
# ============================================

def main():
    """Main bot loop"""
    print("=" * 50)
    print("🤖 جاري تشغيل البوت...")
    print("=" * 50)
    
    # Initialize database
    if not init_database():
        print("❌ فشل في تهيئة قاعدة البيانات!")
        return
    
    print("✅ قاعدة البيانات جاهزة")
    print(f"💳 السعر لكل كود: {PRICE_PER_CODE} نجمة ⭐")
    print(f"📦 عدد الأكواد المتاحة: {len(CODES)}")
    print("=" * 50)
    
    while True:
        try:
            get_updates()
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\n👋 تم إيقاف البوت")
            break
        except Exception as e:
            print(f"❌ خطأ: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
