"""
Web Dashboard for Telegram Bot Statistics
Displays real-time data from PostgreSQL Database
"""

from flask import Flask, render_template_string, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# ============================================
# Configuration
# ============================================
app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

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
        
        # Recent users (last 10)
        cur.execute("""
            SELECT user_id, username, first_name, last_name, join_date, last_activity
            FROM users 
            ORDER BY join_date DESC 
            LIMIT 10
        """)
        recent_users = cur.fetchall()
        
        # Recent purchases (last 10)
        cur.execute("""
            SELECT p.id, p.user_id, u.username, u.first_name, p.code_id, p.price, p.purchase_date
            FROM purchases p
            JOIN users u ON p.user_id = u.user_id
            ORDER BY p.purchase_date DESC
            LIMIT 10
        """)
        recent_purchases = cur.fetchall()
        
        # Users joined today
        cur.execute("""
            SELECT COUNT(*) FROM users 
            WHERE DATE(join_date) = CURRENT_DATE
        """)
        users_today = cur.fetchone()[0]
        
        # Purchases today
        cur.execute("""
            SELECT COUNT(*) FROM purchases 
            WHERE DATE(purchase_date) = CURRENT_DATE
        """)
        purchases_today = cur.fetchone()[0]
        
        # Revenue today
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
            "recent_users": recent_users,
            "recent_purchases": recent_purchases,
            "users_today": users_today,
            "purchases_today": purchases_today,
            "revenue_today": revenue_today
        }
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        if conn:
            conn.close()
        return None


def get_all_users():
    """Get all users"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT u.*, COUNT(p.id) as total_purchases
            FROM users u
            LEFT JOIN purchases p ON u.user_id = p.user_id
            GROUP BY u.user_id
            ORDER BY u.join_date DESC
        """)
        users = cur.fetchall()
        cur.close()
        conn.close()
        return users
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        if conn:
            conn.close()
        return []

# ============================================
# HTML Template
# ============================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم البوت - إحصائيات مباشرة</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            padding: 40px 20px;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .last-update {
            opacity: 0.9;
            font-size: 0.9rem;
            margin-top: 10px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }

        .stat-label {
            color: #666;
            font-size: 1.1rem;
        }

        .stat-subtext {
            color: #999;
            font-size: 0.9rem;
            margin-top: 5px;
        }

        /* Tables */
        .section {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .section-title {
            font-size: 1.8rem;
            color: #667eea;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: right;
            font-weight: 600;
        }

        td {
            padding: 15px;
            border-bottom: 1px solid #eee;
            text-align: right;
        }

        tr:hover {
            background: #f5f7fa;
        }

        .user-badge {
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            display: inline-block;
        }

        .purchase-badge {
            background: #FFD700;
            color: #000;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: bold;
            display: inline-block;
        }

        /* Auto refresh indicator */
        .refresh-indicator {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(255,255,255,0.9);
            padding: 15px 25px;
            border-radius: 50px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            font-size: 0.9rem;
            color: #667eea;
        }

        .refresh-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #4CAF50;
            border-radius: 50%;
            margin-left: 10px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        /* Responsive */
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .stats-grid { grid-template-columns: 1fr; }
            table { font-size: 0.9rem; }
            th, td { padding: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 لوحة تحكم بوت متجر الأكواد</h1>
            <p>إحصائيات وبيانات مباشرة</p>
            <p class="last-update" id="lastUpdate">آخر تحديث: جاري التحميل...</p>
        </header>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-value" id="totalUsers">{{ stats.total_users }}</div>
                <div class="stat-label">إجمالي المستخدمين</div>
                <div class="stat-subtext">+{{ stats.users_today }} اليوم</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">🛒</div>
                <div class="stat-value" id="totalPurchases">{{ stats.total_purchases }}</div>
                <div class="stat-label">إجمالي المشتريات</div>
                <div class="stat-subtext">+{{ stats.purchases_today }} اليوم</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">⭐</div>
                <div class="stat-value" id="totalRevenue">{{ stats.total_revenue }}</div>
                <div class="stat-label">إجمالي النجوم</div>
                <div class="stat-subtext">+{{ stats.revenue_today }} اليوم</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-value">{{ "%.1f"|format((stats.total_purchases / stats.total_users * 100) if stats.total_users > 0 else 0) }}%</div>
                <div class="stat-label">معدل التحويل</div>
                <div class="stat-subtext">مشتريات/مستخدمين</div>
            </div>
        </div>

        <!-- Recent Users -->
        <div class="section">
            <h2 class="section-title">
                <span>👥</span>
                أحدث المستخدمين
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>المعرف</th>
                        <th>الاسم</th>
                        <th>اسم المستخدم</th>
                        <th>تاريخ الانضمام</th>
                        <th>آخر نشاط</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in stats.recent_users %}
                    <tr>
                        <td><span class="user-badge">{{ user[0] }}</span></td>
                        <td>{{ user[2] }} {{ user[3] or '' }}</td>
                        <td>@{{ user[1] or 'غير متوفر' }}</td>
                        <td>{{ user[4].strftime('%Y-%m-%d %H:%M') if user[4] else '-' }}</td>
                        <td>{{ user[5].strftime('%Y-%m-%d %H:%M') if user[5] else '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Recent Purchases -->
        <div class="section">
            <h2 class="section-title">
                <span>🛒</span>
                أحدث المشتريات
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>المستخدم</th>
                        <th>اسم المستخدم</th>
                        <th>الكود</th>
                        <th>السعر</th>
                        <th>التاريخ</th>
                    </tr>
                </thead>
                <tbody>
                    {% for purchase in stats.recent_purchases %}
                    <tr>
                        <td>{{ purchase[0] }}</td>
                        <td>{{ purchase[3] }}</td>
                        <td>@{{ purchase[2] or 'غير متوفر' }}</td>
                        <td><span class="purchase-badge">كود #{{ purchase[4] }}</span></td>
                        <td>{{ purchase[5] }} ⭐</td>
                        <td>{{ purchase[6].strftime('%Y-%m-%d %H:%M') if purchase[6] else '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Auto Refresh Indicator -->
    <div class="refresh-indicator">
        <span class="refresh-dot"></span>
        تحديث تلقائي كل 30 ثانية
    </div>

    <script>
        // Update last update time
        function updateTime() {
            const now = new Date();
            document.getElementById('lastUpdate').textContent = 
                'آخر تحديث: ' + now.toLocaleString('ar-EG');
        }
        
        updateTime();

        // Auto refresh every 30 seconds
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
"""

# ============================================
# Routes
# ============================================

@app.route('/')
def dashboard():
    """Main dashboard page"""
    stats = get_stats()
    
    if not stats:
        return """
        <html dir="rtl">
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>❌ خطأ في الاتصال بقاعدة البيانات</h1>
            <p>تأكد من تشغيل البوت وإعداد قاعدة البيانات بشكل صحيح</p>
        </body>
        </html>
        """, 500
    
    return render_template_string(HTML_TEMPLATE, stats=stats)


@app.route('/api/stats')
def api_stats():
    """API endpoint for stats"""
    stats = get_stats()
    
    if not stats:
        return jsonify({"error": "Database connection failed"}), 500
    
    return jsonify({
        "total_users": stats["total_users"],
        "total_purchases": stats["total_purchases"],
        "total_revenue": stats["total_revenue"],
        "users_today": stats["users_today"],
        "purchases_today": stats["purchases_today"],
        "revenue_today": stats["revenue_today"]
    })


@app.route('/api/users')
def api_users():
    """API endpoint for all users"""
    users = get_all_users()
    
    if not users:
        return jsonify([]), 200
    
    users_list = []
    for user in users:
        users_list.append({
            "user_id": user["user_id"],
            "username": user["username"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "join_date": user["join_date"].isoformat() if user["join_date"] else None,
            "total_purchases": user["total_purchases"]
        })
    
    return jsonify(users_list)


@app.route('/health')
def health_check():
    """Health check endpoint"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    return jsonify({"status": "unhealthy", "database": "disconnected"}), 503

# ============================================
# Main
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 جاري تشغيل لوحة التحكم...")
    print("=" * 50)
    print("📊 الرابط: http://localhost:5000")
    print("🔄 التحديث التلقائي: كل 30 ثانية")
    print("=" * 50)
    
    # Run Flask app
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
