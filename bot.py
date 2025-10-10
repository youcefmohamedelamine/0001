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
PRODUCT_DESCRIPTION = "ملف نصي فريد يحتوي على كلمة أحبك بتصاميم وخطوط جميلة بلغات مختلفة"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    keyboard = [
        [InlineKeyboardButton("🌐 افتح المتجر", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"مرحباً بك في متجر ملفات أحبك! 💖\n\n"
        f"🎁 المنتج: {PRODUCT_NAME}\n"
        f"⭐ السعر: {PRODUCT_PRICE} نجمة تيليجرام\n\n"
        f"📝 الوصف:\n{PRODUCT_DESCRIPTION}\n\n"
        f"اضغط على الزر أدناه لفتح المتجر! 👇"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج البيانات المرسلة من WebApp"""
    try:
        # استخراج البيانات من WebApp
        data = json.loads(update.effective_message.web_app_data.data)
        logger.info(f"📥 تم استقبال بيانات من WebApp: {data}")
        
        # التحقق من نوع العملية
        if data.get('action') == 'create_invoice':
            user = update.effective_user
            
            # إرسال رسالة تأكيد
            await update.message.reply_text(
                "⏳ جاري إنشاء فاتورة الدفع...\n"
                "الرجاء الانتظار..."
            )
            
            # إنشاء رابط فاتورة
            invoice_link = await create_invoice_link(context)
            
            # إرسال رابط الفاتورة للمستخدم
            keyboard = [[InlineKeyboardButton("⭐ ادفع الآن - 1 نجمة ⭐", url=invoice_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "✅ تم إنشاء فاتورتك بنجاح!\n\n"
                f"👤 المستخدم: {user.first_name}\n"
                f"📦 المنتج: {PRODUCT_NAME}\n"
                f"💰 المبلغ: {PRODUCT_PRICE} ⭐\n\n"
                "اضغط على الزر أدناه لإتمام الدفع 👇",
                reply_markup=reply_markup
            )
            
            logger.info(f"✅ تم إرسال رابط الفاتورة للمستخدم {user.id}")
            
        else:
            logger.warning(f"⚠️ عملية غير معروفة: {data.get('action')}")
            await update.message.reply_text("❌ عملية غير صالحة!")
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ خطأ في فك تشفير JSON: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ في معالجة الطلب!\n"
            "الرجاء المحاولة مرة أخرى."
        )
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع!\n"
            "الرجاء التواصل مع الدعم الفني."
        )

async def create_invoice_link(context: ContextTypes.DEFAULT_TYPE):
    """إنشاء رابط فاتورة دفع بالنجوم"""
    try:
        link = await context.bot.create_invoice_link(
            title=PRODUCT_NAME,
            description=PRODUCT_DESCRIPTION,
            payload="love_file_payment",  # معرّف فريد للمنتج
            currency="XTR",  # عملة النجوم
            prices=[LabeledPrice("ملف كلمة أحبك", PRODUCT_PRICE)]
        )
        
        logger.info(f"🔗 تم إنشاء رابط فاتورة: {link}")
        return link
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء الفاتورة: {e}")
        raise

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق قبل إتمام الدفع"""
    query = update.pre_checkout_query
    user = query.from_user
    
    logger.info(f"🔍 التحقق من الدفع للمستخدم {user.id}")
    
    # التحقق من صحة المنتج
    if query.invoice_payload == "love_file_payment":
        await query.answer(ok=True)
        logger.info(f"✅ تم قبول الدفع للمستخدم {user.id}")
    else:
        await query.answer(
            ok=False, 
            error_message="❌ معرّف المنتج غير صحيح!"
        )
        logger.warning(f"⚠️ تم رفض الدفع - معرّف خاطئ: {query.invoice_payload}")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عند نجاح الدفع - إرسال الملف"""
    user = update.message.from_user
    payment_info = update.message.successful_payment
    
    logger.info(f"💰 دفع ناجح من المستخدم {user.username} (ID: {user.id})")
    logger.info(f"📊 معلومات الدفع: {payment_info}")
    
    # محتوى الملف - يمكنك تخصيصه
    file_content = """
╔═══════════════════════════════════════════╗
║                                           ║
║            💖 أحبك 💖                    ║
║        كلمة من القلب ❤️                  ║
║                                           ║
╚═══════════════════════════════════════════╝

═══════════════════════════════════════════

🌍 كلمة "أحبك" بلغات مختلفة:

العربية:    أحبك ❤️
English:    I Love You 💕
Français:   Je t'aime 💗
Español:    Te amo 💖
Deutsch:    Ich liebe dich 💝
Italiano:   Ti amo 💓
日本語:      愛してる 💞
한국어:       사랑해 💗
中文:        我爱你 💖
Русский:    Я люблю тебя 💕
Português:  Eu te amo 💗
हिन्दी:     मैं तुमसे प्यार करता हूँ 💝

═══════════════════════════════════════════

🎨 تصاميم فنية:

    ♡♥♡♥♡ أحبك ♡♥♡♥♡
    
    ❤️ 💛 💚 💙 💜 أحبك 💜 💙 💚 💛 ❤️
    
    ╔═══╗
    ║ ❤️ ║  أحبك
    ╚═══╝
    
    ┏━━━━━━━━━━━━━┓
    ┃  💖 أحبك 💖  ┃
    ┗━━━━━━━━━━━━━┛

═══════════════════════════════════════════

💝 شكراً لشرائك من متجرنا! 

نتمنى أن تعجبك هذه الكلمات الجميلة
ولا تنسى مشاركتها مع من تحب! 💕

═══════════════════════════════════════════

© 2025 متجر ملفات أحبك 💖
جميع الحقوق محفوظة
    """
    
    try:
        # إرسال رسالة شكر
        await update.message.reply_text(
            "🎉 تم الدفع بنجاح!\n\n"
            "✅ تم استلام دفعتك\n"
            "📦 جاري إرسال الملف إليك...\n\n"
            "شكراً لثقتك بنا! 💖"
        )
        
        # حفظ الملف مؤقتاً
        filename = f"احبك_{user.id}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # إرسال الملف
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename="💖_احبك_Love.txt",
                caption=(
                    "💖 إليك ملفك المميز!\n\n"
                    "📄 يحتوي على كلمة أحبك بـ 12 لغة\n"
                    "🎨 مع تصاميم فنية جميلة\n\n"
                    "استمتع به! 🌟"
                )
            )
        
        # حذف الملف المؤقت
        import os
        os.remove(filename)
        
        # إرسال رسالة إضافية
        await update.message.reply_text(
            "✅ تم إرسال الملف بنجاح!\n\n"
            "💡 يمكنك:\n"
            "• فتح الملف ونسخ المحتوى\n"
            "• مشاركته مع أحبائك\n"
            "• استخدامه في رسائلك\n\n"
            "🌟 شكراً لاستخدامك بوتنا!\n"
            "اضغط /start للشراء مرة أخرى"
        )
        
        logger.info(f"✅ تم إرسال الملف بنجاح للمستخدم {user.id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الملف: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ في إرسال الملف!\n"
            "الرجاء التواصل مع الدعم الفني."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    help_text = """
📖 دليل استخدام البوت:

🔹 الخطوات:
1️⃣ اضغط /start لبدء البوت
2️⃣ اضغط على "افتح المتجر"
3️⃣ اختر المنتج واضغط "ادفع الآن"
4️⃣ أكد طلبك في الصفحة
5️⃣ ادفع باستخدام نجوم تيليجرام ⭐
6️⃣ استلم الملف فوراً! 📄

💡 معلومات مهمة:
• السعر: 1 نجمة فقط ⭐
• التسليم: فوري بعد الدفع
• الدفع: آمن 100% عبر تيليجرام

❓ لديك سؤال؟
تواصل مع الدعم الفني

═══════════════════════════════════════
© 2025 متجر ملفات أحبك 💖
    """
    await update.message.reply_text(help_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات البوت - للمطورين فقط"""
    # يمكنك إضافة نظام للتحقق من المطورين
    ADMIN_IDS = []  # ضع IDs المطورين هنا
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ هذا الأمر للمطورين فقط!")
        return
    
    # هنا يمكنك إضافة إحصائيات حقيقية
    stats_text = """
📊 إحصائيات البوت:

👥 عدد المستخدمين: --
💰 إجمالي المبيعات: --
📦 عدد الطلبات: --
⭐ النجوم المكتسبة: --

🕐 آخر تحديث: الآن
    """
    await update.message.reply_text(stats_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام"""
    logger.error(f"❌ حدث خطأ: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ حدث خطأ غير متوقع!\n"
            "الرجاء المحاولة مرة أخرى لاحقاً."
        )

def main():
    """تشغيل البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # معالج بيانات WebApp - هذا المهم!
    application.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data)
    )
    
    # معالجات الدفع
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    )
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    logger.info("🚀 البوت يعمل الآن!")
    logger.info(f"🔗 رابط WebApp: {WEBAPP_URL}")
    logger.info("✅ جاهز لاستقبال الطلبات...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
