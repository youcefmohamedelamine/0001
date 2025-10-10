import asyncio
import logging
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ضع توكن البوت هنا
BOT_TOKEN = "ضع_توكن_البوت_هنا"

# معلومات المنتج
PRODUCT_NAME = "ملف كلمة أحبك"
PRODUCT_PRICE = 1  # سعر بالنجوم
PRODUCT_DESCRIPTION = "احصل على ملف نصي يحتوي على كلمة أحبك بخطوط جميلة"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    keyboard = [
        [InlineKeyboardButton("🌟 شراء الملف (1 نجمة)", callback_data='buy_file')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"مرحباً بك! 👋\n\n"
        f"🎁 المنتج المتاح: {PRODUCT_NAME}\n"
        f"💫 السعر: {PRODUCT_PRICE} نجمة تيليجرام\n\n"
        f"اضغط على الزر أدناه للشراء!"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أزرار الشراء"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'buy_file':
        await send_invoice(query, context)

async def send_invoice(query, context: ContextTypes.DEFAULT_TYPE):
    """إرسال فاتورة الدفع"""
    chat_id = query.message.chat_id
    
    # إنشاء الفاتورة
    title = PRODUCT_NAME
    description = PRODUCT_DESCRIPTION
    payload = "file_payment_payload"
    currency = "XTR"  # عملة نجوم تيليجرام
    
    prices = [LabeledPrice("ملف أحبك", PRODUCT_PRICE)]
    
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # فارغ لنجوم تيليجرام
        currency=currency,
        prices=prices
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق قبل إتمام الدفع"""
    query = update.pre_checkout_query
    
    # يمكنك إضافة فحوصات إضافية هنا
    if query.invoice_payload == "file_payment_payload":
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="حدث خطأ في عملية الدفع")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عند نجاح الدفع، إرسال الملف"""
    user = update.message.from_user
    
    # إنشاء محتوى الملف
    file_content = """
╔═══════════════════════════════╗
║                               ║
║         💖 أحبك 💖           ║
║                               ║
║      كلمة من القلب ❤️        ║
║                               ║
╚═══════════════════════════════╝

أحبك ❤️
I Love You 💕
Je t'aime 💗
Te amo 💖

شكراً لشرائك من بوتنا! 🌟
    """
    
    # حفظ الملف مؤقتاً
    filename = f"احبك_{user.id}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(file_content)
    
    # إرسال رسالة شكر
    await update.message.reply_text(
        "✅ تم الدفع بنجاح! 🎉\n"
        "جاري إرسال الملف إليك..."
    )
    
    # إرسال الملف
    with open(filename, 'rb') as f:
        await update.message.reply_document(
            document=f,
            filename="احبك.txt",
            caption="💖 هذا هو ملفك! استمتع به 🌟"
        )
    
    # حذف الملف المؤقت
    import os
    os.remove(filename)
    
    logger.info(f"تم إرسال الملف للمستخدم {user.username} (ID: {user.id})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    help_text = (
        "📖 كيفية استخدام البوت:\n\n"
        "1️⃣ اضغط على /start\n"
        "2️⃣ اضغط على زر الشراء\n"
        "3️⃣ ادفع باستخدام نجوم تيليجرام ⭐\n"
        "4️⃣ استلم الملف فوراً! 📄\n\n"
        "💡 ملاحظة: تأكد من توفر نجوم كافية في حسابك"
    )
    await update.message.reply_text(help_text)

def main():
    """تشغيل البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # معالج الأزرار
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # معالجات الدفع
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # بدء البوت
    logger.info("البوت يعمل الآن! 🚀")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
