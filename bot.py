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


    def get_leaderboard(self, limit=100):
        """جلب أفضل 100 مستخدم"""
        conn = self._get_connection()
        if not conn:
            return []
    
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT 
                    u.user_id,
                    u.first_name,
                    u.last_name,
                    u.username,
                    u.join_date,
                    COUNT(p.id) as purchase_count,
                    SUM(p.price) as total_spent
                FROM users u
                LEFT JOIN purchases p ON u.user_id = p.user_id
                GROUP BY u.user_id, u.first_name, u.last_name, u.username, u.join_date
                ORDER BY purchase_count DESC, u.join_date ASC
                LIMIT %s
            """, (limit,))
        
            users = cur.fetchall()
            cur.close()
            conn.close()
        
            leaderboard = []
            for idx, user in enumerate(users, 1):
                name = f"{user['first_name']} {user['last_name']}".strip()
                if not name:
                    name = user['username'] or f"User_{user['user_id']}"
            
                leaderboard.append({
                    "rank": idx,
                    "name": name,
                    "purchases": user['purchase_count'] or 0,
                    "join_date": user['join_date'].strftime('%Y-%m-%d') if user['join_date'] else 'Unknown'
                })
        
            return leaderboard
        except Exception as e:
            print(f"❌ خطأ في جلب الليدربورد: {e}")
            if conn:
                conn.close()
            return []

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

        @self.flask_app.route('/api/leaderboard')
        def api_leaderboard():
            leaderboard = self.get_leaderboard(100)
            return jsonify(leaderboard)
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
    <title>🐍 Python Code Shop</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --primary: #00ff88;
            --secondary: #00ccff;
            --dark: #0d0d0d;
            --darker: #050505;
            --card-bg: #1a1a1a;
        }
        
        body {
            font-family: 'Tajawal', sans-serif;
            background: var(--darker);
            color: #fff;
            overflow-x: hidden;
        }
        
        /* Animated Background */
        .bg-animation {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: -1;
            background: linear-gradient(45deg, #0d0d0d, #1a1a1a, #0d0d0d);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .grid-overlay {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            background-image: 
                linear-gradient(rgba(0, 255, 136, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 255, 136, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            z-index: -1;
        }
        
        /* Sidebar Navigation */
        .sidebar {
            position: fixed;
            right: 0;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 80px;
            background: rgba(26, 26, 26, 0.8);
            backdrop-filter: blur(20px);
            border-top: 2px solid var(--primary);
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: center;
            gap: 30px;
            padding: 0 30px;
            z-index: 1000;
        }
        
        .logo-mini {
            font-size: 2.5rem;
            margin-bottom: 0;
            margin-right: 30px;
            animation: float 3s ease-in-out infinite;  
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .nav-icon {
            width: 50px;
            height: 50px;
            margin:  0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            cursor: pointer;
            border-radius: 12px;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .nav-icon:hover, .nav-icon.active {
            background: var(--primary);
            color: var(--darker);
            transform: scale(1.1);
        }
        
        .nav-icon::before {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 70px;
            left: 50px;
            transform: translateX(-50%);
            background: var(--primary);
            color: var(--darker);
            padding: 8px 15px;
            border-radius: 8px;
            font-size: 0.9rem;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        }
        
        .nav-icon:hover::before {
            opacity: 1;
        }
        
        /* Main Content */
        .main-content {
            margin-left: 0;
            margin-right: 0;
            margin-bottom: 100px;
            padding: 40px;
        }
        
        .page {
            display: none;
            animation: pageSlide 0.5s ease;
        }
        
        .page.active { display: block; }
        
        @keyframes pageSlide {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        /* Hero Section - Bento Style */
        .bento-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .bento-box {
            background: var(--card-bg);
            border: 2px solid #2a2a2a;
            border-radius: 20px;
            padding: 30px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .bento-box:hover {
            border-color: var(--primary);
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 255, 136, 0.2);
        }
        
        .bento-large {
            grid-column: span 2;
            grid-row: span 2;
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        
        .bento-wide {
            grid-column: span 2;
        }
        
        .hero-title {
            font-size: 4rem;
            font-weight: 900;
            margin-bottom: 20px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }
        
        .hero-subtitle {
            font-size: 1.3rem;
            color: #888;
            margin-bottom: 30px;
        }
        
        .glow-btn {
            background: var(--primary);
            color: var(--darker);
            padding: 18px 40px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.2rem;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
            transition: all 0.3s ease;
        }
        
        .glow-btn:hover {
            box-shadow: 0 0 50px rgba(0, 255, 136, 0.8);
            transform: scale(1.05);
        }
        
        /* Stats Box */
        .stat-box-modern {
            text-align: center;
        }
        
        .stat-icon-modern {
            font-size: 3rem;
            margin-bottom: 15px;
            filter: drop-shadow(0 0 10px var(--primary));
        }
        
        .stat-value-modern {
            font-size: 2.5rem;
            font-weight: 900;
            color: var(--primary);
            margin: 10px 0;
        }
        
        .stat-label-modern {
            font-size: 0.95rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-change {
            display: inline-block;
            background: rgba(0, 255, 136, 0.1);
            color: var(--primary);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-top: 8px;
        }
        
        /* Products Section - Card Style */
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
        }
        
        .section-title-modern {
            font-size: 2.5rem;
            font-weight: 900;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
        }
        
        .product-card-modern {
            background: var(--card-bg);
            border: 2px solid #2a2a2a;
            border-radius: 20px;
            padding: 30px;
            position: relative;
            transition: all 0.4s ease;
            cursor: pointer;
        }
        
        .product-card-modern::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border-radius: 20px;
            padding: 2px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            opacity: 0;
            transition: opacity 0.4s ease;
        }
        
        .product-card-modern:hover::before {
            opacity: 1;
        }
        
        .product-card-modern:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 50px rgba(0, 255, 136, 0.3);
        }
        
        .product-icon-modern {
            font-size: 4rem;
            margin-bottom: 20px;
            display: block;
        }
        
        .product-name-modern {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 12px;
            color: #fff;
        }
        
        .product-desc-modern {
            color: #888;
            line-height: 1.6;
            margin-bottom: 20px;
            font-size: 0.95rem;
        }
        
        .product-price-modern {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 20px;
            border-top: 1px solid #2a2a2a;
        }
        
        .price-tag-modern {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary);
        }
        
        .buy-icon {
            width: 40px;
            height: 40px;
            background: var(--primary);
            color: var(--darker);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            transition: all 0.3s ease;
        }
        
        .product-card-modern:hover .buy-icon {
            transform: rotate(360deg) scale(1.2);
        }
        
        /* Leaderboard - Modern Table Style */
        .leaderboard-container {
            background: var(--card-bg);
            border: 2px solid #2a2a2a;
            border-radius: 20px;
            padding: 40px;
            margin-top: 40px;
        }
        
        .leaderboard-title {
            font-size: 3rem;
            font-weight: 900;
            text-align: center;
            margin-bottom: 40px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .leaderboard-table {
            width: 100%;
        }
        
        .leaderboard-row {
            display: grid;
            grid-template-columns: 80px 1fr 150px;
            gap: 20px;
            align-items: center;
            padding: 20px;
            margin-bottom: 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            border: 1px solid #2a2a2a;
            transition: all 0.3s ease;
        }
        
        .leaderboard-row:hover {
            background: rgba(0, 255, 136, 0.05);
            border-color: var(--primary);
            transform: translateX(-5px);
        }
        
        .rank-badge {
            font-size: 2rem;
            font-weight: 900;
            text-align: center;
        }
        
        .rank-1 { color: #FFD700; text-shadow: 0 0 20px #FFD700; }
        .rank-2 { color: #C0C0C0; text-shadow: 0 0 20px #C0C0C0; }
        .rank-3 { color: #CD7F32; text-shadow: 0 0 20px #CD7F32; }
        
        .player-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .player-avatar {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            font-weight: bold;
        }
        
        .player-details h3 {
            font-size: 1.2rem;
            margin-bottom: 5px;
        }
        
        .player-details p {
            font-size: 0.85rem;
            color: #888;
        }
        
        .player-stats {
            text-align: left;
        }
        
        .stat-number {
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--primary);
        }
        
        .stat-text {
            font-size: 0.85rem;
            color: #888;
        }
        
        /* Features Grid */
        .features-modern {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin: 60px 0;
        }
        
        .feature-modern {
            background: var(--card-bg);
            border: 2px solid #2a2a2a;
            border-radius: 20px;
            padding: 35px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .feature-modern:hover {
            border-color: var(--primary);
            transform: translateY(-8px);
        }
        
        .feature-icon-modern {
            font-size: 3.5rem;
            margin-bottom: 20px;
            filter: drop-shadow(0 0 15px var(--primary));
        }
        
        .feature-title-modern {
            font-size: 1.3rem;
            font-weight: bold;
            margin-bottom: 12px;
        }
        
        .feature-text-modern {
            color: #888;
            line-height: 1.6;
        }
        
        /* Live Indicator */
        .live-badge {
            position: fixed;
            bottom: 30px;
            left: 30px;
            background: var(--card-bg);
            border: 2px solid var(--primary);
            padding: 12px 25px;
            border-radius: 50px;
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 999;
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.3);
        }
        
        .live-dot {
            width: 10px;
            height: 10px;
            background: var(--primary);
            border-radius: 50%;
            animation: livePulse 2s infinite;
        }
        
        @keyframes livePulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.6; }
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 100px 20px;
        }
        
        .empty-icon {
            font-size: 6rem;
            margin-bottom: 30px;
            opacity: 0.3;
        }
        
        .empty-title {
            font-size: 2rem;
            margin-bottom: 15px;
            color: #888;
        }
        
        .empty-text {
            color: #666;
            font-size: 1.1rem;
        }
        
        /* Responsive */
        @media (max-width: 1200px) {
            .bento-grid { grid-template-columns: repeat(2, 1fr); }
            .bento-large, .bento-wide { grid-column: span 2; }
        }
        
        @media (max-width: 768px) {
            .sidebar { 
                padding: 0 10px;
                height: 70px;
                gap: 10px;
            }
            .logo-mini {
                font-size: 1.8rem;
                margin-right: 10px;
            }
            .nav-icon {
                width: 45px;
                height: 45px;
                font-size: 1.4rem;
            }
            .main-content { margin-right: 0; padding: 20px; }
            .hero-title { font-size: 2.5rem; }
            .bento-grid { grid-template-columns: 1fr; }
            .bento-large, .bento-wide { grid-column: span 1; grid-row: span 1; }
            .products-grid { grid-template-columns: 1fr; }
            .leaderboard-row { 
                grid-template-columns: 50px 1fr 80px; 
                padding: 10px;
                font-size: 0.85rem;
}
            
            .section-title-modern { font-size: 2rem; }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="grid-overlay"></div>
    
    <!-- Sidebar Navigation -->
    <aside class="sidebar">
        <div class="logo-mini">🐍</div>
        <div class="nav-icon active" data-tooltip="الرئيسية" onclick="switchPage('home')">🏠</div>
        <div class="nav-icon" data-tooltip="المتجر" onclick="switchPage('shop')">🛍️</div>
        <div class="nav-icon" data-tooltip="المتصدرين" onclick="switchPage('leaderboard')">🏆</div>
        <div class="nav-icon" data-tooltip="تيليجرام" onclick="window.open('https://t.me/WinterLand_bot', '_blank')">✈️</div>
    </aside>
    
    <!-- Main Content -->
    <main class="main-content">
        <!-- Home Page -->
        <div id="home" class="page active">
            <!-- Bento Grid Hero -->
            <div class="bento-grid">
                <div class="bento-box bento-large">
                    <div class="hero-title">Python Store</div>
                    <p class="hero-subtitle">أكواد برمجية احترافية جاهزة للاستخدام الفوري</p>
                    <a href="https://t.me/WinterLand_bot" class="glow-btn">
                        <span>ابدأ الشراء</span>
                        <span>→</span>
                    </a>
                </div>
                
                <div class="bento-box">
                    <div class="stat-box-modern">
                        <div class="stat-icon-modern">👥</div>
                        <div class="stat-value-modern">{{ stats.total_users }}</div>
                        <div class="stat-label-modern">المستخدمون</div>
                        <div class="stat-change">+{{ stats.users_today }}</div>
                    </div>
                </div>
                
                <div class="bento-box">
                    <div class="stat-box-modern">
                        <div class="stat-icon-modern">🛒</div>
                        <div class="stat-value-modern">{{ stats.total_purchases }}</div>
                        <div class="stat-label-modern">المشتريات</div>
                        <div class="stat-change">+{{ stats.purchases_today }}</div>
                    </div>
                </div>
                
                <div class="bento-box bento-wide">
                    <div class="stat-box-modern">
                        <div class="stat-icon-modern">⭐</div>
                        <div class="stat-value-modern">{{ stats.total_revenue }}</div>
                        <div class="stat-label-modern">إجمالي النجوم المكتسبة</div>
                        <div class="stat-change">+{{ stats.revenue_today }} اليوم</div>
                    </div>
                </div>
            </div>
            
            <!-- Features -->
            <div class="section-header">
                <h2 class="section-title-modern">🔥 لماذا نحن؟</h2>
            </div>
            
            <div class="features-modern">
                <div class="feature-modern">
                    <div class="feature-icon-modern">⚡</div>
                    <h3 class="feature-title-modern">سرعة البرق</h3>
                    <p class="feature-text-modern">استلم الكود خلال ثوانٍ من الدفع</p>
                </div>
                <div class="feature-modern">
                    <div class="feature-icon-modern">🔐</div>
                    <h3 class="feature-title-modern">دفع آمن</h3>
                    <p class="feature-text-modern">عبر نظام نجوم تيليجرام الرسمي</p>
                </div>
                <div class="feature-modern">
                    <div class="feature-icon-modern">💎</div>
                    <h3 class="feature-title-modern">جودة مضمونة</h3>
                    <p class="feature-text-modern">أكواد مختبرة وموثوقة 100%</p>
                </div>
                <div class="feature-modern">
                    <div class="feature-icon-modern">📱</div>
                    <h3 class="feature-title-modern">كل شيء هنا</h3>
                    <p class="feature-text-modern">داخل تيليجرام بدون تطبيقات خارجية</p>
                </div>
            </div>
        </div>
        
        <!-- Shop Page -->
        <div id="shop" class="page">
            <div class="section-header">
                <h2 class="section-title-modern">🛍️ المتجر (10 أكواد)</h2>
            </div>
            
            <div class="products-grid">
                <div class="product-card-modern">
                    <span class="product-icon-modern">🌡️</span>
                    <h3 class="product-name-modern">Temperature Converter</h3>
                    <p class="product-desc-modern">تحويل سريع بين درجات الحرارة المئوية والفهرنهايت</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">🔐</span>
                    <h3 class="product-name-modern">Password Generator</h3>
                    <p class="product-desc-modern">توليد كلمات مرور عشوائية قوية وآمنة</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">📁</span>
                    <h3 class="product-name-modern">File Lister</h3>
                    <p class="product-desc-modern">عرض جميع الملفات في مجلد معين</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">📝</span>
                    <h3 class="product-name-modern">Word Counter</h3>
                    <p class="product-desc-modern">حساب عدد الكلمات والأحرف في النصوص</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">➕</span>
                    <h3 class="product-name-modern">List Summer</h3>
                    <p class="product-desc-modern">جمع جميع الأرقام في قائمة بسرعة</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">🔢</span>
                    <h3 class="product-name-modern">Max Finder</h3>
                    <p class="product-desc-modern">إيجاد أكبر رقم في قائمة من الأرقام</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">🔄</span>
                    <h3 class="product-name-modern">String Reverser</h3>
                    <p class="product-desc-modern">عكس أي نص أو كلمة بضغطة واحدة</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">🎯</span>
                    <h3 class="product-name-modern">Even Checker</h3>
                    <p class="product-desc-modern">التحقق من الأرقام الزوجية والفردية</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">🧹</span>
                    <h3 class="product-name-modern">Duplicate Remover</h3>
                    <p class="product-desc-modern">إزالة العناصر المكررة من القوائم</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
                
                <div class="product-card-modern">
                    <span class="product-icon-modern">🔤</span>
                    <h3 class="product-name-modern">Vowel Counter</h3>
                    <p class="product-desc-modern">عد حروف العلة في النصوص الإنجليزية</p>
                    <div class="product-price-modern">
                        <span class="price-tag-modern">999 ⭐</span>
                        <div class="buy-icon">🛒</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Leaderboard Page -->
        <div id="leaderboard" class="page">
            <div class="leaderboard-container">
                <h1 class="leaderboard-title">🏆 قائمة المتصدرين</h1>
                <div class="leaderboard-table" id="leaderboard-content">
                    <!-- Will be populated by JavaScript -->
                </div>
                <div class="empty-state" id="empty-state" style="display: none;">
                    <div class="empty-icon">📊</div>
                    <h2 class="empty-title">لا توجد بيانات حتى الآن</h2>
                    <p class="empty-text">سيتم عرض أول 100 مستخدم انضموا للمنصة هنا</p>
                </div>
            </div>
        </div>
    </main>
    
    <!-- Live Update Badge -->
    <div class="live-badge">
        <div class="live-dot"></div>
        <span>تحديث تلقائي • 60 ثانية</span>
    </div>
    
    <script>
        // Sort by purchases (if no purchases, show first 100 joined)
        mockUsers.sort((a, b) => {
            if (b.purchases !== a.purchases) {
                return b.purchases - a.purchases;
            }
            return a.id - b.id;
        });
        
        // Page Navigation
        function switchPage(pageName) {
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
            });
            document.getElementById(pageName).classList.add('active');
            
            document.querySelectorAll('.nav-icon').forEach(icon => {
                icon.classList.remove('active');
            });
            event.target.classList.add('active');
            
            if (pageName === 'leaderboard') {
                loadLeaderboard();
            }
            
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        // Load Leaderboard
        // Load Leaderboard
        function loadLeaderboard() {
            const content = document.getElementById('leaderboard-content');
            const emptyState = document.getElementById('empty-state');
    
            // جلب البيانات من API
            fetch('/api/leaderboard')
                .then(response => response.json())
                .then(users => {
                    if (users.length > 0) {
                        content.style.display = 'block';
                        emptyState.style.display = 'none';
                        content.innerHTML = '';
                
                        users.forEach((user) => {
                            const rank = user.rank;
                            let rankDisplay = '#' + rank;
                            let rankClass = '';
                    
                            if (rank === 1) {
                                rankDisplay = '🥇';
                                rankClass = 'rank-1';
                            } else if (rank === 2) {
                                rankDisplay = '🥈';
                                rankClass = 'rank-2';
                            } else if (rank === 3) {
                                rankDisplay = '🥉';
                                rankClass = 'rank-3';
                            }
                    
                            const row = document.createElement('div');
                            row.className = 'leaderboard-row';
                            row.innerHTML = `
                                <div class="rank-badge ${rankClass}">${rankDisplay}</div>
                                <div class="player-info">
                                <div class="player-avatar">${user.name.charAt(0)}</div>
                                    <div class="player-details">
                                        <h3>${user.name}</h3>
                                        <p>انضم في: ${user.join_date}</p>
                                    </div>
                                </div>
                                <div class="player-stats">
                                    <div class="stat-number">${user.purchases}</div>
                                    <div class="stat-text">${user.purchases === 0 ? 'لم يشتري بعد' : user.purchases === 1 ? 'عملية شراء' : 'عملية شراء'}</div>
                                </div>
                            `;
                            content.appendChild(row);
                        });
                    } else {
                        content.style.display = 'none';
                        emptyState.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Error loading leaderboard:', error);
                    emptyState.style.display = 'block';
                });
        }
        
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);
        
        // Initialize animations
        document.addEventListener('DOMContentLoaded', () => {
            const animatedElements = document.querySelectorAll('.bento-box, .product-card-modern, .feature-modern');
            animatedElements.forEach((el, index) => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = `all 0.6s ease ${index * 0.1}s`;
                observer.observe(el);
            });
            
            // Trigger animations after a short delay
            setTimeout(() => {
                animatedElements.forEach(el => {
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                });
            }, 100);
        });
        
        // Auto refresh every 60 seconds
        setTimeout(() => {
            location.reload();
        }, 60000);
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
    port = int(os.getenv("PORT", 5000))
    stats_manager.start_web_dashboard(host='0.0.0.0', port=port, threaded=True)
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
