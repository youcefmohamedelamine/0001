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
