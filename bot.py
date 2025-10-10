import telebot
from telebot import types
import requests
import time
from datetime import datetime
import json

# ضع توكن البوت الخاص بك هنا
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# عنوان محفظة TON الخاصة بك لاستقبال المدفوعات
MERCHANT_WALLET = "YOUR_TON_WALLET_ADDRESS"

# السعر بالـ TON (بالنانو تون: 1 TON = 1,000,000,000 nanoTON)
PRICE_TON = 1.0
PRICE_NANOTON = int(PRICE_TON * 1_000_000_000)

# TON API endpoint (استخدام TonCenter API)
TON_API_URL = "https://toncenter.com/api/v2"
TON_API_KEY = "YOUR_TONCENTER_API_KEY"  # احصل عليه من @tonapibot

bot = telebot.TeleBot(BOT_TOKEN)

# قاموس لتتبع المستخدمين والمدفوعات
user_sessions = {}
paid_users = {}

def create_tonkeeper_link(amount, comment, recipient):
    """إنشاء رابط TonKeeper للدفع"""
    # تحويل المبلغ إلى nanoTON
    amount_nano = int(amount * 1_000_000_000)
    
    # إنشاء رابط TonKeeper
    tonkeeper_url = f"https://app.tonkeeper.com/transfer/{recipient}?amount={amount_nano}&text={comment}"
    
    # رابط TON الأساسي (يعمل مع معظم المحافظ)
    ton_url = f"ton://transfer/{recipient}?amount={amount_nano}&text={comment}"
    
    return tonkeeper_url, ton_url

def check_transaction(wallet_address, expected_amount, comment):
    """التحقق من المعاملة باستخدام TonCenter API"""
    try:
        headers = {}
        if TON_API_KEY and TON_API_KEY != "YOUR_TONCENTER_API_KEY":
            headers['X-API-Key'] = TON_API_KEY
        
        # جلب آخر المعاملات
        url = f"{TON_API_URL}/getTransactions"
        params = {
            'address': MERCHANT_WALLET,
            'limit': 10
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                transactions = data['result']
                
                # البحث عن المعاملة المطابقة
                for tx in transactions:
                    # التحقق من أن المعاملة واردة
                    if tx.get('in_msg'):
                        in_msg = tx['in_msg']
                        
                        # التحقق من المبلغ
                        value = int(in_msg.get('value', 0))
                        
                        # التحقق من التعليق
                        msg_data = in_msg.get('message', '')
                        
                        # التحقق من المطابقة
                        if value >= expected_amount and comment in msg_data:
                            return True, tx
                
        return False, None
    except Exception as e:
        print(f"Error checking transaction: {e}")
        return False, None

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = """
🌹 مرحباً بك في بوت "أحبك" 🌹

💝 يمكنك شراء كلمة "أحبك" الخاصة بك مقابل 1 TON فقط!

✨ مزايا البوت:
• دفع سهل وسريع عبر TonKeeper
• تأكيد فوري للدفع
• آمن ومضمون 100%

استخدم الأوامر التالية:
/buy - لشراء كلمة "أحبك"
/check - للتحقق من حالة الدفع
/wallet - لعرض معلومات المحفظة
/help - للمساعدة
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['wallet'])
def wallet_info(message):
    wallet_text = f"""
💳 معلومات المحفظة:

محفظة التاجر: 
<code>{MERCHANT_WALLET}</code>

يمكنك الدفع باستخدام:
• TonKeeper
• Tonhub
• MyTonWallet
• أي محفظة TON أخرى

استخدم /buy للحصول على رابط الدفع المباشر
    """
    bot.send_message(message.chat.id, wallet_text, parse_mode='HTML')

@bot.message_handler(commands=['buy'])
def buy(message):
    user_id = message.from_user.id
    
    # إنشاء معرف فريد للمعاملة
    transaction_id = f"love_{user_id}_{int(time.time())}"
    
    # حفظ معلومات الجلسة
    user_sessions[user_id] = {
        'transaction_id': transaction_id,
        'amount': PRICE_TON,
        'timestamp': time.time(),
        'confirmed': False
    }
    
    # إنشاء روابط الدفع
    tonkeeper_url, ton_url = create_tonkeeper_link(
        PRICE_TON,
        transaction_id,
        MERCHANT_WALLET
    )
    
    # إنشاء لوحة المفاتيح
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    tonkeeper_btn = types.InlineKeyboardButton(
        text="💎 افتح في TonKeeper",
        url=tonkeeper_url
    )
    
    ton_btn = types.InlineKeyboardButton(
        text="📱 افتح في محفظة TON",
        url=ton_url
    )
    
    check_btn = types.InlineKeyboardButton(
        text="✅ تحققت من الدفع",
        callback_data=f"verify_{user_id}"
    )
    
    manual_check_btn = types.InlineKeyboardButton(
        text="🔍 تحقق يدوي",
        callback_data=f"manual_check_{user_id}"
    )
    
    markup.add(tonkeeper_btn, ton_btn)
    markup.add(check_btn)
    markup.add(manual_check_btn)
    
    payment_text = f"""
💰 طلب دفع جديد

السعر: {PRICE_TON} TON
معرف المعاملة: <code>{transaction_id}</code>

📝 خطوات الدفع:

1️⃣ اضغط على "افتح في TonKeeper" أدناه
2️⃣ ستفتح محفظة TonKeeper تلقائياً
3️⃣ تحقق من المبلغ والعنوان
4️⃣ أكمل عملية الدفع
5️⃣ ارجع للبوت واضغط "تحققت من الدفع"

⚠️ هام:
• تأكد من نسخ معرف المعاملة في رسالة الدفع
• المبلغ المطلوب: {PRICE_TON} TON بالضبط
• لا تقم بتعديل أي معلومات في صفحة الدفع

العنوان: <code>{MERCHANT_WALLET}</code>
    """
    
    bot.send_message(message.chat.id, payment_text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_'))
def verify_payment(call):
    user_id = int(call.data.split('_')[1])
    
    if user_id not in user_sessions:
        bot.answer_callback_query(call.id, "❌ لم يتم العثور على طلب دفع. استخدم /buy أولاً")
        return
    
    session = user_sessions[user_id]
    transaction_id = session['transaction_id']
    
    bot.answer_callback_query(call.id, "🔍 جاري التحقق من الدفع...")
    
    # التحقق من المعاملة
    found, tx_data = check_transaction(
        MERCHANT_WALLET,
        PRICE_NANOTON,
        transaction_id
    )
    
    if found:
        # تم العثور على الدفع
        session['confirmed'] = True
        paid_users[user_id] = {
            'paid': True,
            'timestamp': datetime.now(),
            'amount': PRICE_TON,
            'transaction_id': transaction_id
        }
        
        success_text = """
✅ تم التحقق من الدفع بنجاح! 

💝💝💝 أحبك 💝💝💝

شكراً لك على الشراء! 🌹✨
معاملتك تم تأكيدها على شبكة TON

هل تريد شراء المزيد؟ استخدم /buy
        """
        
        bot.send_message(call.message.chat.id, success_text)
        
        # حذف الجلسة
        del user_sessions[user_id]
    else:
        # لم يتم العثور على الدفع
        retry_text = """
⏳ لم نتمكن من تأكيد الدفع بعد

الأسباب المحتملة:
• المعاملة لا تزال قيد المعالجة على الشبكة
• لم يتم إرسال المبلغ الصحيح
• معرف المعاملة غير صحيح

انتظر قليلاً ثم اضغط "تحققت من الدفع" مرة أخرى
أو استخدم "تحقق يدوي" للمراجعة
        """
        
        bot.send_message(call.message.chat.id, retry_text)

@bot.callback_query_handler(func=lambda call: call.data.startswith('manual_check_'))
def manual_check(call):
    user_id = int(call.data.split('_')[2])
    
    if user_id not in user_sessions:
        bot.answer_callback_query(call.id, "❌ لم يتم العثور على طلب دفع")
        return
    
    session = user_sessions[user_id]
    
    manual_text = f"""
🔍 معلومات للتحقق اليدوي:

معرف المعاملة: <code>{session['transaction_id']}</code>
المبلغ المطلوب: {session['amount']} TON
عنوان المحفظة: <code>{MERCHANT_WALLET}</code>

يمكنك التحقق من المعاملة على:
• TON Explorer: https://tonscan.org/address/{MERCHANT_WALLET}
• TonWhales: https://tonwhales.com/explorer/address/{MERCHANT_WALLET}

إذا قمت بالدفع، انتظر 1-2 دقيقة ثم اضغط "تحققت من الدفع"
    """
    
    bot.answer_callback_query(call.id, "✅ تم إرسال معلومات التحقق")
    bot.send_message(call.message.chat.id, manual_text, parse_mode='HTML')

@bot.message_handler(commands=['check'])
def check_status(message):
    user_id = message.from_user.id
    
    if user_id in paid_users and paid_users[user_id]['paid']:
        status_text = f"""
✅ حالة الدفع: مدفوع ومؤكد

💝 أحبك 💝

معلومات الدفع:
• تاريخ الدفع: {paid_users[user_id]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
• المبلغ: {paid_users[user_id]['amount']} TON
• معرف المعاملة: <code>{paid_users[user_id]['transaction_id']}</code>
        """
    elif user_id in user_sessions:
        status_text = """
⏳ حالة الدفع: في انتظار التأكيد

لديك طلب دفع نشط. استخدم الزر "تحققت من الدفع" للتحقق
أو استخدم /buy لإنشاء طلب جديد
        """
    else:
        status_text = """
❌ لم يتم العثور على دفع

استخدم /buy لشراء كلمة "أحبك"
        """
    
    bot.send_message(message.chat.id, status_text, parse_mode='HTML')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📖 دليل الاستخدام:

🔹 الأوامر المتاحة:
/start - بدء البوت
/buy - شراء كلمة "أحبك" (1 TON)
/check - التحقق من حالة الدفع
/wallet - عرض معلومات المحفظة
/help - عرض هذه المساعدة

🔹 كيفية الدفع:
1. استخدم /buy للحصول على رابط الدفع
2. اضغط "افتح في TonKeeper"
3. أكمل الدفع في محفظتك
4. عد للبوت واضغط "تحققت من الدفع"

🔹 المحافظ المدعومة:
• TonKeeper ✅ (موصى به)
• Tonhub ✅
• MyTonWallet ✅
• أي محفظة TON أخرى ✅

💡 نصائح:
• تأكد من وجود رصيد كافٍ في محفظتك
• انتظر 1-2 دقيقة لتأكيد المعاملة
• احتفظ بمعرف المعاملة للرجوع إليه

للدعم: @your_support_username
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "استخدم /help لمعرفة الأوامر المتاحة 💝")

if __name__ == '__main__':
    print("🤖 البوت يعمل الآن...")
    print(f"💳 محفظة التاجر: {MERCHANT_WALLET}")
    print(f"💰 السعر: {PRICE_TON} TON")
    bot.infinity_polling()
