import telebot
from telebot import types
import time
from datetime import datetime

# ضع توكن البوت الخاص بك هنا
BOT_TOKEN = "7253548907:AAGCTAfnGBK9ub_mar_ePG-1OhZ45APIR9w"

# عنوان محفظة TON الخاصة بك لاستقبال المدفوعات
WALLET_ADDRESS = "UQD43SvwO1tguKvIeDkDixxBIF_hOLGiKXU7rZtak9FZsWG3"

# السعر بالـ TON
PRICE = 1.0

bot = telebot.TeleBot(BOT_TOKEN)

# قاموس لتتبع المستخدمين الذين دفعوا
paid_users = {}

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = """
🌹 مرحباً بك في بوت "أحبك" 🌹

💝 يمكنك شراء كلمة "أحبك" الخاصة بك مقابل 1 TON فقط!

استخدم الأوامر التالية:
/buy - لشراء كلمة "أحبك"
/check - للتحقق من حالة الدفع
/help - للمساعدة
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['buy'])
def buy(message):
    user_id = message.from_user.id
    
    # إنشاء لوحة مفاتيح مع زر الدفع
    markup = types.InlineKeyboardMarkup()
    payment_btn = types.InlineKeyboardButton(
        text=f"💳 ادفع {PRICE} TON",
        url=f"ton://transfer/{WALLET_ADDRESS}?amount={int(PRICE * 1e9)}&text=payment_{user_id}"
    )
    check_btn = types.InlineKeyboardButton(
        text="✅ تحققت من الدفع",
        callback_data=f"check_{user_id}"
    )
    markup.add(payment_btn)
    markup.add(check_btn)
    
    payment_text = f"""
💰 معلومات الدفع:

السعر: {PRICE} TON
عنوان المحفظة: {WALLET_ADDRESS}

📝 تعليمات الدفع:
1. اضغط على زر "ادفع {PRICE} TON" أدناه
2. أكمل عملية الدفع من محفظتك
3. بعد إتمام الدفع، اضغط على "تحققت من الدفع"

⚠️ تأكد من إرسال المبلغ الصحيح وإضافة المعرف: payment_{user_id}
    """
    
    bot.send_message(message.chat.id, payment_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def check_payment(call):
    user_id = int(call.data.split('_')[1])
    
    # هنا يجب عليك التحقق من الدفع الفعلي عبر TON blockchain
    # في هذا المثال، سنفترض أن الدفع تم بنجاح بعد 5 ثوانٍ
    
    bot.answer_callback_query(call.id, "جاري التحقق من الدفع... ⏳")
    
    # محاكاة التحقق (في الواقع، يجب استخدام TON API)
    # يمكنك استخدام tonutils أو toncenter API للتحقق الفعلي
    
    # إذا تم التحقق من الدفع:
    paid_users[user_id] = {
        'paid': True,
        'timestamp': datetime.now(),
        'amount': PRICE
    }
    
    success_text = """
✅ تم استلام الدفع بنجاح! 

💝 أحبك 💝

شكراً لك على الشراء! 🌹
هل تريد شراء المزيد؟ استخدم /buy
    """
    
    bot.send_message(call.message.chat.id, success_text)

@bot.message_handler(commands=['check'])
def check_status(message):
    user_id = message.from_user.id
    
    if user_id in paid_users and paid_users[user_id]['paid']:
        status_text = f"""
✅ حالة الدفع: مدفوع

💝 أحبك 💝

تاريخ الدفع: {paid_users[user_id]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
المبلغ: {paid_users[user_id]['amount']} TON
        """
    else:
        status_text = """
❌ لم يتم العثور على دفع

استخدم /buy لشراء كلمة "أحبك"
        """
    
    bot.reply_to(message, status_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📖 المساعدة:

الأوامر المتاحة:
/start - بدء البوت
/buy - شراء كلمة "أحبك" مقابل 1 TON
/check - التحقق من حالة الدفع
/help - عرض هذه المساعدة

💡 ملاحظات:
- السعر: 1 TON
- الدفع يتم عبر محفظة TON
- بعد الدفع، ستحصل على كلمة "أحبك" الخاصة بك

للدعم: @your_support_username
    """
    bot.reply_to(message, help_text)

# معالج للرسائل العادية
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "استخدم /help لمعرفة الأوامر المتاحة 💝")

if __name__ == '__main__':
    print("🤖 البوت يعمل الآن...")
    bot.infinity_polling()
