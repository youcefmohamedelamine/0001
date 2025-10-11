"""
Simple Telegram Bot - Sell Python Codes for Stars
Works with any Python version - uses only requests library
"""

import requests
import time
import json

# Configuration
BOT_TOKEN = "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
PRICE_PER_CODE = 999

# Simple Python codes for sale
CODES = {
    "1": {
        "name": "Temperature Converter",
        "desc": "Convert between Celsius and Fahrenheit",
        "code": "def celsius_to_fahrenheit(c):\n    return (c * 9/5) + 32\n\ndef fahrenheit_to_celsius(f):\n    return (f - 32) * 5/9\n\nprint(celsius_to_fahrenheit(25))\nprint(fahrenheit_to_celsius(77))"
    },
    "2": {
        "name": "Random Password",
        "desc": "Generate random password",
        "code": "import random\nimport string\n\ndef gen_pass(length=8):\n    chars = string.ascii_letters + string.digits\n    return ''.join(random.choice(chars) for i in range(length))\n\nprint(gen_pass(12))"
    },
    "3": {
        "name": "List Files",
        "desc": "List all files in directory",
        "code": "import os\n\ndef list_files(path='.'):\n    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]\n    return files\n\nprint(list_files())"
    },
    "4": {
        "name": "Count Words",
        "desc": "Count words in text",
        "code": "def count_words(text):\n    words = text.split()\n    return len(words)\n\ntext = 'Hello world from Python'\nprint(f'Words: {count_words(text)}')"
    },
    "5": {
        "name": "Sum Numbers",
        "desc": "Sum all numbers in a list",
        "code": "def sum_list(numbers):\n    total = 0\n    for num in numbers:\n        total += num\n    return total\n\nmy_list = [1, 2, 3, 4, 5]\nprint(f'Sum: {sum_list(my_list)}')"
    },
    "6": {
        "name": "Find Max",
        "desc": "Find maximum number in list",
        "code": "def find_max(numbers):\n    if not numbers:\n        return None\n    max_num = numbers[0]\n    for num in numbers:\n        if num > max_num:\n            max_num = num\n    return max_num\n\nprint(find_max([3, 7, 2, 9, 1]))"
    },
    "7": {
        "name": "Reverse String",
        "desc": "Reverse any string",
        "code": "def reverse_string(text):\n    return text[::-1]\n\ntext = 'Hello Python'\nprint(reverse_string(text))"
    },
    "8": {
        "name": "Is Even",
        "desc": "Check if number is even",
        "code": "def is_even(num):\n    return num % 2 == 0\n\nfor i in range(1, 11):\n    print(f'{i} is even: {is_even(i)}')"
    },
    "9": {
        "name": "Remove Duplicates",
        "desc": "Remove duplicate items from list",
        "code": "def remove_duplicates(items):\n    return list(set(items))\n\nmy_list = [1, 2, 2, 3, 3, 4, 5, 5]\nprint(remove_duplicates(my_list))"
    },
    "10": {
        "name": "Count Vowels",
        "desc": "Count vowels in a string",
        "code": "def count_vowels(text):\n    vowels = 'aeiouAEIOU'\n    count = 0\n    for char in text:\n        if char in vowels:\n            count += 1\n    return count\n\nprint(count_vowels('Hello World'))"
    }
}

# Store purchases (in production, use a database)
purchases = {}
last_update_id = 0


def send_message(chat_id, text, reply_markup=None):
    """Send text message"""
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None


def send_invoice(chat_id, code_id):
    """Send payment invoice"""
    code = CODES[code_id]
    url = f"{BASE_URL}/sendInvoice"
    
    payload = {
        "chat_id": chat_id,
        "title": code["name"],
        "description": code["desc"],
        "payload": f"code_{code_id}_{chat_id}",
        "currency": "XTR",  # Telegram Stars
        "prices": [{"label": code["name"], "amount": PRICE_PER_CODE}]
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending invoice: {e}")
        return None


def answer_pre_checkout(pre_checkout_id, ok=True):
    """Answer pre-checkout query"""
    url = f"{BASE_URL}/answerPreCheckoutQuery"
    data = {
        "pre_checkout_query_id": pre_checkout_id,
        "ok": ok
    }
    requests.post(url, json=data)


def handle_start(chat_id):
    """Handle /start command"""
    text = """
🐍 *Welcome to Python Code Shop!*

Buy simple Python codes for *999 Stars* each!

*Available Codes:*
1. Temperature Converter
2. Random Password Generator
3. List Files in Directory
4. Count Words in Text
5. Sum Numbers in List
6. Find Maximum Number
7. Reverse String
8. Check if Even Number
9. Remove Duplicates
10. Count Vowels

*Commands:*
/catalog - Browse all codes
/buy [1-10] - Buy a code
/mycodes - Your purchased codes
"""
    send_message(chat_id, text)


def handle_catalog(chat_id):
    """Show catalog"""
    text = "📚 *Available Python Codes:*\n\n"
    for code_id, code in CODES.items():
        text += f"{code_id}. *{code['name']}* - {code['desc']}\n"
    
    text += f"\n💰 Price: *{PRICE_PER_CODE} Stars* each\n"
    text += "\nUse /buy [number] to purchase"
    
    send_message(chat_id, text)


def handle_buy(chat_id, code_id):
    """Handle buy command"""
    if code_id not in CODES:
        send_message(chat_id, "❌ Invalid code number. Use /catalog to see available codes.")
        return
    
    # Check if already purchased
    if chat_id in purchases and code_id in purchases[chat_id]:
        code = CODES[code_id]
        text = f"✅ You already own this code!\n\n*{code['name']}*\n\n```python\n{code['code']}\n```"
        send_message(chat_id, text)
        return
    
    # Send invoice
    send_invoice(chat_id, code_id)


def handle_mycodes(chat_id):
    """Show purchased codes"""
    if chat_id not in purchases or not purchases[chat_id]:
        send_message(chat_id, "📭 You haven't purchased any codes yet.\n\nUse /catalog to browse!")
        return
    
    text = "📚 *Your Purchased Codes:*\n\n"
    for code_id in purchases[chat_id]:
        code = CODES[code_id]
        text += f"✅ {code['name']}\n"
    
    text += "\nUse /resend [number] to get a code again"
    send_message(chat_id, text)


def handle_resend(chat_id, code_id):
    """Resend purchased code"""
    if chat_id not in purchases or code_id not in purchases[chat_id]:
        send_message(chat_id, "❌ You don't own this code. Use /buy to purchase it!")
        return
    
    code = CODES[code_id]
    text = f"📦 *{code['name']}*\n\n```python\n{code['code']}\n```"
    send_message(chat_id, text)


def handle_successful_payment(chat_id, payload):
    """Handle successful payment"""
    parts = payload.split("_")
    code_id = parts[1]
    
    # Store purchase
    if chat_id not in purchases:
        purchases[chat_id] = []
    purchases[chat_id].append(code_id)
    
    # Send the code
    code = CODES[code_id]
    text = f"""
✅ *Payment Successful!*

Thank you for your purchase!

📦 *{code['name']}*

Here's your Python code:

```python
{code['code']}
```

🎉 Enjoy your code!
Use /catalog to buy more!
"""
    send_message(chat_id, text)


def process_update(update):
    """Process incoming update"""
    global purchases
    
    # Handle messages
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        
        # Handle successful payment
        if "successful_payment" in message:
            payload = message["successful_payment"]["invoice_payload"]
            handle_successful_payment(chat_id, payload)
            return
        
        # Handle commands
        if "text" in message:
            text = message["text"]
            
            if text == "/start":
                handle_start(chat_id)
            
            elif text == "/catalog":
                handle_catalog(chat_id)
            
            elif text.startswith("/buy"):
                parts = text.split()
                if len(parts) > 1:
                    code_id = parts[1]
                    handle_buy(chat_id, code_id)
                else:
                    send_message(chat_id, "❌ Please specify code number: /buy [1-10]")
            
            elif text == "/mycodes":
                handle_mycodes(chat_id)
            
            elif text.startswith("/resend"):
                parts = text.split()
                if len(parts) > 1:
                    code_id = parts[1]
                    handle_resend(chat_id, code_id)
                else:
                    send_message(chat_id, "❌ Please specify code number: /resend [1-10]")
    
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
        print(f"Error getting updates: {e}")
        return False


def main():
    """Main bot loop"""
    print("🤖 Bot is running...")
    print(f"Bot Token: {BOT_TOKEN[:10]}...")
    
    while True:
        try:
            get_updates()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
