import asyncio
import logging
import json
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ضع توكن البوت هنا
BOT_TOKEN = "7253548907:AAE3jhMGY5lY-B6lLtouJpqXPs0RepUIF2w"

# رابط صفحة الويب
WEBAPP_URL = "https://youcefmohamedelamine.github.io/0001/index.html"

# معلومات المنتج
PRODUCT_NAME = "ملف كلمة أحبك"
PRODUCT_PRICE = 1  # سعر بالنجوم
PRODUCT_DESCRIPTION = "احصل على ملف نصي يحتوي على كلمة أحبك بخطوط جميلة"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    keyboard = [
        [InlineKeyboardButton("🌐 افتح المتجر", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"مرحباً بك! 👋\n\n"
        f"🎁 المنتج المتاح: {PRODUCT_NAME}\n"
        f"💫 السعر: {PRODUCT_PRICE} نجمة تيليجرام\n\n"
        f"اضغط على الزر لفتح المتجر والشراء مباشرة!"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج البيانات المرسلة من WebApp"""
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        logger.info(f"تم استقبال بيانات من WebApp: {data}")
        
        if data.get('action') == 'request_invoice':
            # إنشاء رابط فاتورة
            invoice_link = await create_invoice_link(context)
            
            # إرسال رابط الفاتورة للمستخدم
            keyboard = [[InlineKeyboardButton("💳 ادفع الآن", url=invoice_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "✅ تم إنشاء فاتورتك!\n"
                "اضغط على الزر للدفع 👇",
                reply_markup=reply_markup
            )
            
    except json.JSONDecodeError:
        logger.error("خطأ في فك تشفير بيانات JSON")
        await update.message.reply_text("❌ حدث خطأ في معالجة الطلب!")

async def create_invoice_link(context: ContextTypes.DEFAULT_TYPE):
    """إنشاء رابط فاتورة دفع"""
    title = PRODUCT_NAME
    description = PRODUCT_DESCRIPTION
    payload = "file_payment_payload"
    currency = "XTR"
    prices = [LabeledPrice("ملف أحبك", PRODUCT_PRICE)]
    
    link = await context.bot.create_invoice_link(
        title=title,
        description=description,
        payload=payload,
        provider_token="",
        currency=currency,
        prices=prices
    )
    
    return link

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق قبل إتمام الدفع"""
    query = update.pre_checkout_query
    
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
Ich liebe dich 💝
Ti amo 💓
愛してる 💞
사랑해 💗

═══════════════════════════════

شكراً لشرائك من بوتنا! 🌟
نتمنى أن تعجبك هذه الكلمات الجميلة 💝

═══════════════════════════════
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
        "2️⃣ افتح المتجر\n"
        "3️⃣ اضغط زر الشراء في الصفحة\n"
        "4️⃣ ادفع باستخدام نجوم تيليجرام ⭐\n"
        "5️⃣ استلم الملف فوراً! 📄\n\n"
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
    
    # معالج بيانات WebApp
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # معالجات الدفع
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # بدء البوت
    logger.info("البوت يعمل الآن! 🚀")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
