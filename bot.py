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


import psycopg2
from flask import Flask, jsonify, render_template_string
import threading
import os
from datetime import datetime
class StatsManager:
    """
    كلاس شامل لإدارة الإحصائيات وعرضها عبر الويب
    """
    
    def __init__(self, database_url):
        """
        تهيئة الكلاس
        
        Args:
            database_url (str): رابط قاعدة البيانات PostgreSQL
        """
        self.database_url = database_url
        self.flask_app = None
        self._init_flask_app()
    # ============================================
    # Database Methods
    # ============================================
    def _get_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
            return None
    
    def get_stats(self):
        """
        جلب الإحصائيات الكاملة
        
        Returns:
            dict: قاموس يحتوي على جميع الإحصائيات
        """
        conn = self._get_connection()
        if not conn:
            return self._empty_stats()
        
        try:
            cur = conn.cursor()
            
            # إجمالي المستخدمين
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            
            # إجمالي المشتريات
            cur.execute("SELECT COUNT(*) FROM purchases")
            total_purchases = cur.fetchone()[0]
            
            # إجمالي الإيرادات
            cur.execute("SELECT SUM(price) FROM purchases")
            total_revenue = cur.fetchone()[0] or 0
            
            # مستخدمين اليوم
            cur.execute("""
                SELECT COUNT(*) FROM users 
                WHERE DATE(join_date) = CURRENT_DATE
            """)
            users_today = cur.fetchone()[0]
            
            # مشتريات اليوم
            cur.execute("""
                SELECT COUNT(*) FROM purchases 
                WHERE DATE(purchase_date) = CURRENT_DATE
            """)
            purchases_today = cur.fetchone()[0]
            
            # إيرادات اليوم
            cur.execute("""
                SELECT SUM(price) FROM purchases 
                WHERE DATE(purchase_date) = CURRENT_DATE
            """)
            revenue_today = cur.fetchone()[0] or 0
            
            cur.close()
            conn.close()
            
            return {
                "total_users": total_users,
                "total_purchases": total_purchases,
                "total_revenue": total_revenue,
                "users_today": users_today,
                "purchases_today": purchases_today,
                "revenue_today": revenue_today
            }
        except Exception as e:
            print(f"❌ خطأ في جلب الإحصائيات: {e}")
            if conn:
                conn.close()
            return self._empty_stats()
    
    def _empty_stats(self):
        """إرجاع إحصائيات فارغة في حالة الخطأ"""
        return {
            "total_users": 0,
            "total_purchases": 0,
            "total_revenue": 0,
            "users_today": 0,
            "purchases_today": 0,
            "revenue_today": 0
        }
    
    def check_db_health(self):
        """
        فحص صحة قاعدة البيانات
        
        Returns:
            bool: True إذا كانت قاعدة البيانات تعمل
        """
        conn = self._get_connection()
        if conn:
            conn.close()
            return True
        return False
    
    # ============================================
    # Flask Web Dashboard
    # ============================================
    
    def _init_flask_app(self):
        """تهيئة تطبيق Flask"""
        self.flask_app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """إعداد مسارات Flask"""
        
        @self.flask_app.route('/')
        def main_page():
            stats = self.get_stats()
            return render_template_string(self._get_html_template(), stats=stats)
        
        @self.flask_app.route('/api/stats')
        def api_stats():
            stats = self.get_stats()
            return jsonify(stats)
        
        @self.flask_app.route('/health')
        def health_check():
            if self.check_db_health():
                return jsonify({"status": "healthy", "database": "connected"}), 200
            return jsonify({"status": "unhealthy", "database": "disconnected"}), 503
    
    def start_web_dashboard(self, host='0.0.0.0', port=5000, debug=False, threaded=True):
        """
        تشغيل لوحة التحكم على الويب
        
        Args:
            host (str): عنوان الاستضافة
            port (int): رقم المنفذ
            debug (bool): وضع التطوير
            threaded (bool): True لتشغيله في thread منفصل (لا يوقف البوت)
        """
        if threaded:
            thread = threading.Thread(
                target=self._run_flask,
                args=(host, port, debug),
                daemon=True
            )
            thread.start()
            print(f"✅ لوحة التحكم تعمل في الخلفية على: http://{host}:{port}")
        else:
            self._run_flask(host, port, debug)
    
    def _run_flask(self, host, port, debug):
        """تشغيل Flask"""
        print("=" * 50)
        print("🌐 جاري تشغيل لوحة التحكم...")
        print(f"🔗 الرابط: http://{host}:{port}")
        print("=" * 50)
        self.flask_app.run(host=host, port=port, debug=debug)
    
    # ============================================
    # HTML Template - Beautiful Landing Page
    # ============================================
    
    def _get_html_template(self):
        """قالب HTML الكامل للصفحة الرئيسية"""
        return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجر أكواد Python - بوت تيليجرام</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
            overflow-x: hidden;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        header {
            text-align: center;
            padding: 60px 20px 40px;
            color: white;
            animation: fadeInDown 1s ease;
        }
        
        .logo { font-size: 80px; margin-bottom: 20px; animation: bounce 2s infinite; }
        
        h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle { font-size: 1.3rem; opacity: 0.9; margin-bottom: 30px; }
        
        .cta-button {
            display: inline-block;
            background: linear-gradient(45deg, #FFD700, #FFA500);
            color: #000;
            padding: 18px 50px;
            border-radius: 50px;
            text-decoration: none;
            font-size: 1.3rem;
            font-weight: bold;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            margin-top: 20px;
        }
        
        .cta-button:hover {
            transform: translateY(-5px) scale(1.05);
            box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        }
        
        .live-stats {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 30px;
            padding: 40px;
            margin: 40px 0;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            animation: fadeInUp 1s ease;
        }
        
        .stats-title {
            text-align: center;
            font-size: 2rem;
            color: #667eea;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .pulse-dot {
            width: 12px;
            height: 12px;
            background: #4CAF50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .stat-box {
            text-align: center;
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            color: white;
            transition: transform 0.3s ease;
        }
        
        .stat-box:hover { transform: translateY(-5px); }
        .stat-icon { font-size: 2.5rem; margin-bottom: 10px; }
        .stat-number { font-size: 2.5rem; font-weight: bold; margin: 10px 0; }
        .stat-label { font-size: 1rem; opacity: 0.9; }
        
        .stat-today {
            font-size: 0.85rem;
            margin-top: 5px;
            opacity: 0.8;
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 15px;
            display: inline-block;
        }
        
        .features {
            background: white;
            border-radius: 30px;
            padding: 60px 40px;
            margin: 40px 0;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            animation: fadeInUp 1s ease;
        }
        
        .section-title {
            text-align: center;
            font-size: 2.5rem;
            color: #667eea;
            margin-bottom: 50px;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }
        
        .feature-card {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
        }
        
        .feature-icon { font-size: 4rem; margin-bottom: 20px; }
        .feature-title { font-size: 1.4rem; color: #667eea; margin-bottom: 10px; }
        .feature-desc { color: #666; line-height: 1.6; }
        
        .codes-section {
            background: white;
            border-radius: 30px;
            padding: 60px 40px;
            margin: 40px 0;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }
        
        .codes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 40px;
        }
        
        .code-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 20px;
            color: white;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .code-card::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            transition: all 0.5s ease;
        }
        
        .code-card:hover::before { transform: translate(-25%, -25%); }
        
        .code-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        }
        
        .code-emoji { font-size: 3rem; margin-bottom: 15px; }
        .code-name { font-size: 1.5rem; margin-bottom: 10px; font-weight: bold; }
        .code-desc { opacity: 0.9; margin-bottom: 20px; line-height: 1.5; }
        
        .price-tag {
            display: inline-flex;
            align-items: center;
            background: rgba(255, 215, 0, 0.9);
            color: #000;
            padding: 12px 25px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 1.2rem;
            gap: 8px;
        }
        
        .pricing {
            text-align: center;
            padding: 60px 20px;
            color: white;
        }
        
        .price-box {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 30px;
            padding: 50px;
            max-width: 500px;
            margin: 30px auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }
        
        .price-amount { font-size: 4rem; font-weight: bold; margin: 20px 0; }
        .price-per { font-size: 1.2rem; opacity: 0.9; }
        
        footer {
            text-align: center;
            padding: 40px 20px;
            color: white;
            opacity: 0.8;
        }
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        
        .stars {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        }
        
        .star {
            position: absolute;
            color: gold;
            font-size: 20px;
            animation: twinkle 3s infinite;
        }
        
        @keyframes twinkle {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }
        
        .refresh-indicator {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(255,255,255,0.95);
            padding: 12px 20px;
            border-radius: 50px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            font-size: 0.85rem;
            color: #667eea;
            z-index: 1000;
        }
        
        .refresh-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #4CAF50;
            border-radius: 50%;
            margin-left: 8px;
            animation: pulse 2s infinite;
        }
        
        @media (max-width: 768px) {
            h1 { font-size: 2rem; }
            .subtitle { font-size: 1rem; }
            .section-title { font-size: 1.8rem; }
            .price-amount { font-size: 3rem; }
            .codes-grid, .features-grid, .stats-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="stars" id="stars"></div>

    <div class="container">
        <header>
            <div class="logo">🐍</div>
            <h1>متجر أكواد Python</h1>
            <p class="subtitle">اشترِ أكواد برمجية جاهزة عبر بوت تيليجرام ⭐</p>
            <a href="https://t.me/WinterLand_bot" class="cta-button">ابدأ الآن على تيليجرام</a>
        </header>

        <section class="live-stats">
            <h2 class="stats-title">
                <span class="pulse-dot"></span>
                📊 إحصائيات مباشرة
            </h2>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-icon">👥</div>
                    <div class="stat-number">{{ stats.total_users }}</div>
                    <div class="stat-label">إجمالي المستخدمين</div>
                    <div class="stat-today">+{{ stats.users_today }} اليوم</div>
                </div>
                <div class="stat-box">
                    <div class="stat-icon">🛒</div>
                    <div class="stat-number">{{ stats.total_purchases }}</div>
                    <div class="stat-label">إجمالي المشتريات</div>
                    <div class="stat-today">+{{ stats.purchases_today }} اليوم</div>
                </div>
                <div class="stat-box">
                    <div class="stat-icon">⭐</div>
                    <div class="stat-number">{{ stats.total_revenue }}</div>
                    <div class="stat-label">إجمالي النجوم</div>
                    <div class="stat-today">+{{ stats.revenue_today }} اليوم</div>
                </div>
            </div>
        </section>

        <section class="features">
            <h2 class="section-title">✨ لماذا تختارنا؟</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <h3 class="feature-title">سريع وسهل</h3>
                    <p class="feature-desc">احصل على الكود فوراً بعد الدفع مباشرة</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔒</div>
                    <h3 class="feature-title">آمن 100%</h3>
                    <p class="feature-desc">الدفع عبر نظام نجوم تيليجرام الآمن</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💎</div>
                    <h3 class="feature-title">جودة عالية</h3>
                    <p class="feature-desc">أكواد مختبرة وجاهزة للاستخدام</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📱</div>
                    <h3 class="feature-title">داخل تيليجرام</h3>
                    <p class="feature-desc">لا حاجة لتطبيقات خارجية</p>
                </div>
            </div>
        </section>

        <section class="codes-section">
            <h2 class="section-title">🛍️ الأكواد المتاحة (10 أكواد)</h2>
            <div class="codes-grid">
                <div class="code-card">
                    <div class="code-emoji">🌡️</div>
                    <div class="code-name">Temperature Converter</div>
                    <p class="code-desc">تحويل بين درجات الحرارة المئوية والفهرنهايت</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">🔐</div>
                    <div class="code-name">Password Generator</div>
                    <p class="code-desc">توليد كلمات مرور عشوائية وآمنة</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">📁</div>
                    <div class="code-name">File Lister</div>
                    <p class="code-desc">عرض جميع الملفات في مجلد معين</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">📝</div>
                    <div class="code-name">Word Counter</div>
                    <p class="code-desc">حساب عدد الكلمات في أي نص</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">➕</div>
                    <div class="code-name">List Summer</div>
                    <p class="code-desc">جمع جميع الأرقام في قائمة</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">🔢</div>
                    <div class="code-name">Max Finder</div>
                    <p class="code-desc">إيجاد أكبر رقم في قائمة</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">🔄</div>
                    <div class="code-name">String Reverser</div>
                    <p class="code-desc">عكس أي نص بسهولة</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">🎯</div>
                    <div class="code-name">Even Checker</div>
                    <p class="code-desc">التحقق من الأرقام الزوجية والفردية</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">🧹</div>
                    <div class="code-name">Duplicate Remover</div>
                    <p class="code-desc">إزالة العناصر المكررة من القوائم</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
                <div class="code-card">
                    <div class="code-emoji">🔤</div>
                    <div class="code-name">Vowel Counter</div>
                    <p class="code-desc">عد حروف العلة في النصوص</p>
                    <div class="price-tag">999 ⭐</div>
                </div>
            </div>
        </section>

        <section class="pricing">
            <h2 class="section-title">💰 السعر</h2>
            <div class="price-box">
                <p class="price-per">كل كود مقابل</p>
                <div class="price-amount">999 ⭐</div>
                <p class="price-per">نجمة تيليجرام فقط!</p>
            </div>
            <a href="https://t.me/WinterLand_bot" class="cta-button">اشترِ الآن</a>
        </section>

        <footer>
            <p>© 2025 متجر أكواد Python | جميع الحقوق محفوظة</p>
            <p style="margin-top: 10px;">صُنع بـ ❤️ للمبرمجين العرب</p>
        </footer>
    </div>

    <div class="refresh-indicator">
        <span class="refresh-dot"></span>
        تحديث تلقائي كل 60 ثانية
    </div>

    <script>
        const starsContainer = document.getElementById('stars');
        for (let i = 0; i < 50; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.textContent = '⭐';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 3 + 's';
            starsContainer.appendChild(star);
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.code-card, .feature-card').forEach(card => {
            observer.observe(card);
        });

        setTimeout(() => location.reload(), 60000);
    </script>
</body>
</html>
        """






# ============================================
# Configuration
# ============================================
BOT_TOKEN = "7580086418:AAGi6mVgzONAl1koEbXfk13eDYTzCeMdDWg"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
PRICE_PER_CODE = 999

# Database connection from Railway environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
stats_manager = StatsManager(DATABASE_URL)

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
    stats_manager.start_web_dashboard(port=5000, threaded=True)
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
