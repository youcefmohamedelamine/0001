"""
Telegram Bot - Sell Python Codes for Stars
This bot sells 10 different Python code examples for 999 Telegram Stars each
"""

from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes
import json

# Your Bot Token from BotFather
BOT_TOKEN = "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg"

# Price in Telegram Stars (1 Star = 1 unit)
PRICE_PER_CODE = 999

# Available Python Codes for Sale
PYTHON_CODES = {
    "1": {
        "name": "Password Generator",
        "description": "Generate secure random passwords with customizable length and characters",
        "price": PRICE_PER_CODE,
        "code": """import random
import string

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

# Usage
print(generate_password(16))"""
    },
    "2": {
        "name": "File Organizer",
        "description": "Automatically organize files in folders by extension",
        "price": PRICE_PER_CODE,
        "code": """import os
import shutil

def organize_files(directory):
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            extension = filename.split('.')[-1]
            folder = os.path.join(directory, extension.upper())
            
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            shutil.move(
                os.path.join(directory, filename),
                os.path.join(folder, filename)
            )
    print("Files organized!")

# Usage
organize_files("./my_folder")"""
    },
    "3": {
        "name": "QR Code Generator",
        "description": "Create QR codes from text or URLs",
        "price": PRICE_PER_CODE,
        "code": """import qrcode

def create_qr_code(data, filename="qrcode.png"):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"QR Code saved as {filename}")

# Usage
create_qr_code("https://example.com")"""
    },
    "4": {
        "name": "Email Validator",
        "description": "Validate email addresses using regex",
        "price": PRICE_PER_CODE,
        "code": """import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email):
        return True
    return False

# Usage
emails = ["test@example.com", "invalid.email", "user@domain.co"]
for email in emails:
    print(f"{email}: {validate_email(email)}")"""
    },
    "5": {
        "name": "Weather API Client",
        "description": "Fetch weather data from OpenWeatherMap API",
        "price": PRICE_PER_CODE,
        "code": """import requests

def get_weather(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200:
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"{city}: {temp}°C, {desc}"
    return "City not found"

# Usage
# api_key = "YOUR_API_KEY"
# print(get_weather("London", api_key))"""
    },
    "6": {
        "name": "URL Shortener",
        "description": "Shorten URLs using TinyURL API",
        "price": PRICE_PER_CODE,
        "code": """import requests

def shorten_url(long_url):
    api_url = f"http://tinyurl.com/api-create.php?url={long_url}"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        return response.text
    return "Error shortening URL"

# Usage
long_url = "https://www.example.com/very/long/url/here"
short_url = shorten_url(long_url)
print(f"Short URL: {short_url}")"""
    },
    "7": {
        "name": "PDF to Text Converter",
        "description": "Extract text from PDF files",
        "price": PRICE_PER_CODE,
        "code": """import PyPDF2

def pdf_to_text(pdf_path):
    text = ""
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    return text

# Usage
content = pdf_to_text("document.pdf")
print(content)"""
    },
    "8": {
        "name": "YouTube Video Downloader",
        "description": "Download YouTube videos using pytube",
        "price": PRICE_PER_CODE,
        "code": """from pytube import YouTube

def download_video(url, path="./downloads"):
    yt = YouTube(url)
    stream = yt.streams.get_highest_resolution()
    
    print(f"Downloading: {yt.title}")
    stream.download(path)
    print("Download complete!")

# Usage
url = "https://www.youtube.com/watch?v=VIDEO_ID"
download_video(url)"""
    },
    "9": {
        "name": "Image Resizer",
        "description": "Resize images to specified dimensions",
        "price": PRICE_PER_CODE,
        "code": """from PIL import Image

def resize_image(input_path, output_path, width, height):
    img = Image.open(input_path)
    resized_img = img.resize((width, height), Image.LANCZOS)
    resized_img.save(output_path)
    print(f"Image resized and saved to {output_path}")

# Usage
resize_image("input.jpg", "output.jpg", 800, 600)"""
    },
    "10": {
        "name": "JSON to CSV Converter",
        "description": "Convert JSON files to CSV format",
        "price": PRICE_PER_CODE,
        "code": """import json
import csv

def json_to_csv(json_file, csv_file):
    with open(json_file, 'r') as jf:
        data = json.load(jf)
    
    with open(csv_file, 'w', newline='') as cf:
        if isinstance(data, list) and len(data) > 0:
            writer = csv.DictWriter(cf, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    print(f"Converted {json_file} to {csv_file}")

# Usage
json_to_csv("data.json", "output.csv")"""
    }
}

# Store purchased codes per user
user_purchases = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Welcome message"""
    welcome_text = """
🐍 **Welcome to Python Code Shop!**

Buy premium Python code examples for only **999 Stars** each!

📚 **Available Codes:**
1. Password Generator
2. File Organizer
3. QR Code Generator
4. Email Validator
5. Weather API Client
6. URL Shortener
7. PDF to Text Converter
8. YouTube Video Downloader
9. Image Resizer
10. JSON to CSV Converter

Use /catalog to browse all codes
Use /buy [number] to purchase a code
Use /help for more information
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show catalog with inline buttons"""
    keyboard = []
    
    for code_id, code_info in PYTHON_CODES.items():
        button = InlineKeyboardButton(
            f"⭐ {code_info['name']} - {code_info['price']} Stars",
            callback_data=f"buy_{code_id}"
        )
        keyboard.append([button])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛍️ **Select a code to purchase:**\n\nClick on any code below to see details and buy!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("buy_"):
        code_id = query.data.split("_")[1]
        code_info = PYTHON_CODES.get(code_id)
        
        if code_info:
            details_text = f"""
📦 **{code_info['name']}**

📝 Description: {code_info['description']}
💰 Price: **{code_info['price']} Stars**

To purchase, use command:
/buy {code_id}
"""
            await query.edit_message_text(details_text, parse_mode='Markdown')


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command"""
    if not context.args:
        await update.message.reply_text("❌ Please specify code number: /buy [1-10]")
        return
    
    code_id = context.args[0]
    
    if code_id not in PYTHON_CODES:
        await update.message.reply_text("❌ Invalid code number. Use /catalog to see available codes.")
        return
    
    code_info = PYTHON_CODES[code_id]
    user_id = update.effective_user.id
    
    # Check if already purchased
    if user_id in user_purchases and code_id in user_purchases[user_id]:
        await update.message.reply_text(
            f"✅ You already own this code!\n\nHere it is again:\n\n```python\n{code_info['code']}\n```",
            parse_mode='Markdown'
        )
        return
    
    # Create invoice
    title = code_info['name']
    description = code_info['description']
    payload = f"code_{code_id}_{user_id}"
    currency = "XTR"  # Telegram Stars currency
    prices = [LabeledPrice(label=title, amount=code_info['price'])]
    
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Empty for Stars
        currency=currency,
        prices=prices
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pre-checkout query"""
    query = update.pre_checkout_query
    
    # Always approve for this demo
    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment"""
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    
    # Extract code_id and user_id from payload
    parts = payload.split("_")
    code_id = parts[1]
    user_id = int(parts[2])
    
    # Store purchase
    if user_id not in user_purchases:
        user_purchases[user_id] = []
    user_purchases[user_id].append(code_id)
    
    # Send the code
    code_info = PYTHON_CODES[code_id]
    
    success_message = f"""
✅ **Payment Successful!**

Thank you for your purchase!

📦 **{code_info['name']}**

Here's your Python code:

```python
{code_info['code']}
```

Enjoy your code! 🎉
Use /catalog to buy more codes!
"""
    
    await update.message.reply_text(success_message, parse_mode='Markdown')


async def my_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's purchased codes"""
    user_id = update.effective_user.id
    
    if user_id not in user_purchases or not user_purchases[user_id]:
        await update.message.reply_text("📭 You haven't purchased any codes yet.\n\nUse /catalog to browse!")
        return
    
    codes_list = "📚 **Your Purchased Codes:**\n\n"
    
    for code_id in user_purchases[user_id]:
        code_info = PYTHON_CODES[code_id]
        codes_list += f"✅ {code_info['name']}\n"
    
    codes_list += "\n💡 Use /resend [number] to get a code again"
    
    await update.message.reply_text(codes_list, parse_mode='Markdown')


async def resend_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resend a purchased code"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("❌ Please specify code number: /resend [1-10]")
        return
    
    code_id = context.args[0]
    
    if user_id not in user_purchases or code_id not in user_purchases[user_id]:
        await update.message.reply_text("❌ You don't own this code. Use /buy to purchase it!")
        return
    
    code_info = PYTHON_CODES[code_id]
    
    await update.message.reply_text(
        f"📦 **{code_info['name']}**\n\n```python\n{code_info['code']}\n```",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
🤖 **Bot Commands:**

/start - Welcome message
/catalog - Browse all codes
/buy [number] - Purchase a code
/mycodes - View your purchased codes
/resend [number] - Get a purchased code again
/help - Show this help message

💳 **Payment:**
All codes cost **999 Telegram Stars**
You can buy Stars in the Telegram app

📧 **Support:**
If you have any issues, contact @YourUsername
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


def main():
    """Start the bot"""
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catalog", catalog))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("mycodes", my_codes))
    app.add_handler(CommandHandler("resend", resend_code))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # Start bot
    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
