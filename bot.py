"""
🤖 بوت Telegram لبيع الملفات مع Mini App
"""

import telebot
from telebot import types
import io
from flask import Flask, render_template_string, request, jsonify
from threading import Thread
import os

# ========================================
# إعدادات البوت
# ========================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7253548907:AAE3jhMGY5lY-B6lLtouJpqXPs0RepUIF2w")
WEB_APP_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "0001-production.up.railway.app")

if not WEB_APP_URL.startswith('http'):
    WEB_APP_URL = f"https://{WEB_APP_URL}"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# قائمة الملفات
FILES = {
    "python": {
        "name": "script.py",
        "content": "# ملف Python فارغ\n# جاهز للكتابة!\n\n",
        "icon": "🐍",
        "description": "ملف Python فارغ جاهز للبرمجة"
    },
    "javascript": {
        "name": "script.js",
        "content": "// ملف JavaScript فارغ\n// ابدأ البرمجة هنا!\n\n",
        "icon": "📜",
        "description": "ملف JavaScript للمشاريع"
    },
    "html": {
        "name": "index.html",
        "content": "<!DOCTYPE html>\n<html>\n<head>\n    <title>صفحة جديدة</title>\n</head>\n<body>\n    <!-- المحتوى هنا -->\n</body>\n</html>",
        "icon": "🌐",
        "description": "ملف HTML لموقعك"
    },
    "css": {
        "name": "style.css",
        "content": "/* ملف CSS فارغ */\n/* أضف تنسيقاتك هنا */\n\n",
        "icon": "🎨",
        "description": "ملف CSS للتصميم"
    },
    "json": {
        "name": "data.json",
        "content": "{\n    \"data\": []\n}",
        "icon": "📊",
        "description": "ملف JSON لتخزين البيانات"
    },
    "cpp": {
        "name": "main.cpp",
        "content": "#include <iostream>\nusing namespace std;\n\nint main() {\n    // اكتب الكود هنا\n    return 0;\n}",
        "icon": "⚡",
        "description": "ملف C++ للبرمجة"
    },
    "java": {
        "name": "Main.java",
        "content": "public class Main {\n    public static void main(String[] args) {\n        // اكتب الكود هنا\n    }\n}",
        "icon": "☕",
        "description": "ملف Java للبرمجة"
    },
    "php": {
        "name": "index.php",
        "content": "<?php\n// ملف PHP فارغ\n// ابدأ البرمجة!\n?>",
        "icon": "🐘",
        "description": "ملف PHP للسيرفر"
    },
    "sql": {
        "name": "database.sql",
        "content": "-- ملف SQL فارغ\n-- اكتب استعلامات SQL هنا\n\n",
        "icon": "🗄️",
        "description": "ملف SQL لقاعدة البيانات"
    },
    "txt": {
        "name": "notes.txt",
        "content": "ملف نصي فارغ\nجاهز للكتابة!\n",
        "icon": "📝",
        "description": "ملف نصي بسيط"
    }
}

PRICE = 999
stats = {"total_sales": 0, "total_revenue": 0}
pending_purchases = {}

# ========================================
# واجهة الويب HTML
# ========================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 متجر الملفات البرمجية</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--tg-theme-bg-color, linear-gradient(135deg, #667eea 0%, #764ba2 100%));
            color: var(--tg-theme-text-color, #333);
            min-height: 100vh;
            padding: 15px;
            padding-bottom: 80px;
            direction: rtl;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: var(--tg-theme-text-color, white);
            margin-bottom: 30px;
            animation: fadeInDown 0.5s;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .header p {
            font-size: 1em;
            opacity: 0.9;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: var(--tg-theme-secondary-bg-color, rgba(255,255,255,0.95));
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            color: var(--tg-theme-button-color, #667eea);
            font-size: 1.5em;
            margin-bottom: 3px;
        }
        
        .stat-card p {
            font-size: 0.75em;
            opacity: 0.8;
        }
        
        .products {
            display: grid;
            gap: 15px;
        }
        
        .product-card {
            background: var(--tg-theme-secondary-bg-color, white);
            border-radius: 15px;
            padding: 15px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s;
            animation: fadeIn 0.5s;
        }
        
        .product-card:active {
            transform: scale(0.98);
        }
        
        .product-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        
        .product-icon {
            font-size: 2.5em;
        }
        
        .product-info {
            flex: 1;
        }
        
        .product-name {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 3px;
        }
        
        .product-description {
            font-size: 0.85em;
            opacity: 0.8;
        }
        
        .product-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid rgba(0,0,0,0.1);
        }
        
        .product-price {
            color: var(--tg-theme-button-color, #667eea);
            font-weight: bold;
            font-size: 1.1em;
        }

        .buy-button {
            background: var(--tg-theme-button-color, #0088cc);
            color: var(--tg-theme-button-text-color, white);
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        .buy-button:active {
            opacity: 0.8;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 متجر الملفات</h1>
            <p>اختر الملف واشتريه بالنجوم ⭐</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{{ stats.total_sales }}</h3>
                <p>المبيعات</p>
            </div>
            <div class="stat-card">
                <h3>{{ stats.total_revenue }}</h3>
                <p>النجوم ⭐</p>
            </div>
            <div class="stat-card">
                <h3>10</h3>
                <p>ملفات</p>
            </div>
        </div>
        
        <div class="products" id="products">
            {% for file_id, file_info in files.items() %}
            <div class="product-card">
                <div class="product-header">
                    <div class="product-icon">{{ file_info.icon }}</div>
                    <div class="product-info">
                        <div class="product-name">{{ file_info.name }}</div>
                        <div class="product-description">{{ file_info.description }}</div>
                    </div>
                </div>
                <div class="product-footer">
                    <div class="product-price">999 ⭐</div>
                    <button class="buy-button" onclick="buyFile('{{ file_id }}', '{{ file_info.name }}')">
                        🛒 اشتري
                    </button>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();

        const userId = tg.initDataUnsafe?.user?.id;

        function buyFile(fileId, fileName) {
            if (!userId) {
                tg.showAlert('❌ خطأ في التعرف على المستخدم!');
                return;
            }

            tg.showConfirm(
                `هل تريد شراء ${fileName} مقابل 999 نجمة؟`,
                (confirmed) => {
                    if (confirmed) {
                        purchaseFile(fileId, fileName);
                    }
                }
            );
        }

        async function purchaseFile(fileId, fileName) {
            try {
                tg.MainButton.setText('جاري المعالجة...').show();
                
                const response = await fetch('/api/purchase', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        file_id: fileId,
                        init_data: tg.initData
                    })
                });

                const data = await response.json();
                
                tg.MainButton.hide();

                if (data.success) {
                    tg.showAlert('✅ ' + data.message, () => {
                        tg.close();
                    });
                } else {
                    tg.showAlert('❌ ' + data.message);
                }
            } catch (error) {
                tg.MainButton.hide();
                tg.showAlert('❌ حدث خطأ، حاول مرة أخرى');
            }
        }

        document.body.style.backgroundColor = tg.themeParams.bg_color || '#667eea';
    </script>
</body>
</html>
"""

# ========================================
# Flask Routes
# ========================================

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, files=FILES, stats=stats)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'bot': 'running'})

@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    data = request.json
    user_id = data.get('user_id')
    file_id = data.get('file_id')
    
    if not user_id or not file_id:
        return jsonify({'success': False, 'message': 'بيانات غير مكتملة!'})
    
    if file_id not in FILES:
        return jsonify({'success': False, 'message': 'الملف غير موجود!'})
    
    pending_purchases[user_id] = file_id
    
    try:
        file_info = FILES[file_id]
        
        bot.send_invoice(
            chat_id=user_id,
            title=file_info['name'],
            description=file_info['description'],
            invoice_payload=f"webapp_purchase_{file_id}",
            provider_token="",
            currency="XTR",
            prices=[
                types.LabeledPrice(label=file_info['name'], amount=PRICE)
            ]
        )
        
        return jsonify({
            'success': True, 
            'message': 'تم إرسال الفاتورة! أكمل الدفع في المحادثة'
        })
        
    except Exception as e:
        print(f"خطأ: {e}")
        return jsonify({
            'success': False, 
            'message': 'حدث خطأ في إرسال الفاتورة!'
        })

# ========================================
# Bot Handlers
# ========================================

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = f"""
🎉 أهلاً بك في متجر الملفات البرمجية!

💎 لدينا 10 أنواع من الملفات الجاهزة
💰 السعر: {PRICE} نجمة ⭐ لكل ملف

اضغط الزر أدناه لتصفح المتجر:
    """
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app_btn = types.KeyboardButton(
        text="🛍️ تصفح المتجر",
        web_app=types.WebAppInfo(url=WEB_APP_URL)
    )
    markup.row(web_app_btn)
    
    direct_btn = types.KeyboardButton(text="📱 الشراء المباشر")
    markup.row(direct_btn)
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📱 الشراء المباشر")
def direct_purchase(message):
    text = "📁 **الملفات المتوفرة:**\n\nاختر الملف الذي تريده:\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for file_id, file_info in FILES.items():
        btn = types.InlineKeyboardButton(
            f"{file_info['icon']} {file_info['name']}", 
            callback_data=f"buy_{file_id}"
        )
        buttons.append(btn)
    
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_purchase(call):
    file_id = call.data.replace('buy_', '')
    
    if file_id not in FILES:
        bot.answer_callback_query(call.id, "خطأ!")
        return
    
    file_info = FILES[file_id]
    
    try:
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=file_info['name'],
            description=file_info['description'],
            invoice_payload=f"direct_{file_id}",
            provider_token="",
            currency="XTR",
            prices=[
                types.LabeledPrice(label=file_info['name'], amount=PRICE)
            ]
        )
        
        bot.answer_callback_query(call.id, "✅ تم إرسال الفاتورة!")
        
    except Exception as e:
        print(f"خطأ: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ", show_alert=True)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    
    if payload.startswith('webapp_purchase_'):
        file_id = payload.replace('webapp_purchase_', '')
    elif payload.startswith('direct_'):
        file_id = payload.replace('direct_', '')
    else:
        bot.send_message(message.chat.id, "❌ خطأ في معالجة الطلب!")
        return
    
    if file_id in FILES:
        file_info = FILES[file_id]
        
        stats['total_sales'] += 1
        stats['total_revenue'] += PRICE
        
        success_text = f"""
✅ **تم الدفع بنجاح!**

🎉 شكراً لشرائك {file_info['icon']} {file_info['name']}

الملف سيصلك الآن...
        """
        
        bot.send_message(message.chat.id, success_text, parse_mode='Markdown')
        
        file_content = file_info['content'].encode('utf-8')
        file_obj = io.BytesIO(file_content)
        file_obj.name = file_info['name']
        
        bot.send_document(
            message.chat.id,
            file_obj,
            caption=f"✨ إليك ملفك: {file_info['name']}\n\nشكراً لك! 💜"
        )
        
        print(f"✅ تم بيع {file_info['name']} للمستخدم {message.from_user.first_name}")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📚 **مساعدة البوت**

**الأوامر:**
• /start - البداية وفتح المتجر
• /help - هذه المساعدة

**كيف تشتري:**
1️⃣ اضغط "🛍️ تصفح المتجر" لفتح الموقع داخل Telegram
2️⃣ أو اضغط "📱 الشراء المباشر" للشراء من البوت

💰 السعر: 999 نجمة ⭐ لكل ملف
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# ========================================
# تشغيل التطبيق
# ========================================

def run_bot():
    print("🤖 البوت يعمل الآن...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"خطأ في البوت: {e}")
            import time
            time.sleep(15)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 بدء تشغيل التطبيق على Railway...")
    print(f"🌐 Web App URL: {WEB_APP_URL}")
    print("=" * 50)
    
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
