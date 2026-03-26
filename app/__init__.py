from flask import Flask, g, session, send_from_directory
from .config import Config
from .db import get_db, init_db, seed_admin, seed_reference_data
from .helpers import ensure_csrf_token, format_currency, load_current_user


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)
    app.config['BASE_DIR'] = Config.BASE_DIR if hasattr(Config, 'BASE_DIR') else None
    app.jinja_env.filters['egp'] = format_currency

    # تسجيل الـ blueprints
    from .auth import bp as auth_bp
    from .users import bp as users_bp
    from .donations import bp as donations_bp
    from .admin import bp as admin_bp
    from .notifications import bp as notifications_bp
    from .reports import bp as reports_bp
    from .certificates import bp as certificates_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(donations_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(certificates_bp)

    # تهيئة قاعدة البيانات
    init_db(app)
    seed_reference_data(app)
    seed_admin(app)

    @app.before_request
    def _bootstrap():
        load_current_user(app)
        ensure_csrf_token()

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' data:"
        return response

    @app.context_processor
    def inject_globals():
        return {
            'current_user': getattr(g, 'current_user', None),
            'csrf_token': session.get('_csrf_token'),
            'goal_amount': app.config.get('GOAL_AMOUNT', 100000),
            'app_name': app.config.get('APP_NAME', 'صندوق الدفعة 109'),
            'telegram_bot_username': app.config.get('TELEGRAM_BOT_USERNAME', ''),
        }

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['BASE_DIR'] / 'uploads', filename)

    @app.route('/health')
    def health():
        db = get_db(app)
        db.execute('SELECT 1').fetchone()
        return {'status': 'ok'}

    # ==================== إضافة مسار API للتحقق من رقم الهاتف ====================
    @app.route('/api/check-phone', methods=['GET'])
    def api_check_phone():
        from flask import request, jsonify
        from .db import get_db
        phone = request.args.get('phone')
        if not phone:
            return jsonify({'exists': False, 'error': 'Phone number required'}), 400
        
        db = get_db()
        user = db.execute('SELECT id FROM users WHERE phone = ?', (phone,)).fetchone()
        return jsonify({'exists': user is not None})

    # ==================== إضافة مسار API لإرسال كود استرجاع كلمة السر ====================
    @app.route('/api/send-reset-code', methods=['POST'])
    def api_send_reset_code():
        from flask import request, jsonify
        from .db import get_db
        import random
        import string
        from datetime import datetime, timedelta
        
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({'success': False, 'message': 'رقم الهاتف مطلوب'}), 400
        
        db = get_db()
        user = db.execute('SELECT id, full_name FROM users WHERE phone = ?', (phone,)).fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'لا يوجد حساب مسجل بهذا الرقم'}), 404
        
        reset_code = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now() + timedelta(minutes=10)
        
        # حذف أي كود سابق
        db.execute('DELETE FROM reset_codes WHERE user_id = ?', (user['id'],))
        
        # حفظ الكود الجديد
        db.execute(
            'INSERT INTO reset_codes (user_id, code, expires_at) VALUES (?, ?, ?)',
            (user['id'], reset_code, expires_at)
        )
        
        # في الإنتاج، أرسل الكود عبر SMS أو Telegram
        print(f"Reset code for {phone}: {reset_code}")
        
        return jsonify({'success': True, 'message': 'تم إرسال كود التحقق'})

    # ==================== إضافة مسار API لإعادة تعيين كلمة السر ====================
    @app.route('/api/reset-password', methods=['POST'])
    def api_reset_password():
        from flask import request, jsonify
        from .db import get_db
        from werkzeug.security import generate_password_hash
        from datetime import datetime
        
        data = request.get_json()
        phone = data.get('phone')
        code = data.get('code')
        new_password = data.get('new_password')
        
        if not all([phone, code, new_password]):
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'}), 400
        
        db = get_db()
        user = db.execute('SELECT id FROM users WHERE phone = ?', (phone,)).fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'لا يوجد حساب مسجل بهذا الرقم'}), 404
        
        reset_code = db.execute(
            'SELECT * FROM reset_codes WHERE user_id = ? AND code = ?',
            (user['id'], code)
        ).fetchone()
        
        if not reset_code:
            return jsonify({'success': False, 'message': 'كود التحقق غير صحيح'}), 400
        
        expires_at = datetime.fromisoformat(reset_code['expires_at'])
        if expires_at < datetime.now():
            return jsonify({'success': False, 'message': 'انتهت صلاحية الكود'}), 400
        
        # تحديث كلمة المرور
        hashed_password = generate_password_hash(new_password)
        db.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user['id']))
        
        # حذف الكود بعد الاستخدام
        db.execute('DELETE FROM reset_codes WHERE id = ?', (reset_code['id'],))
        
        return jsonify({'success': True, 'message': 'تم تغيير كلمة المرور بنجاح'})

    # ==================== إضافة مسار API للإحصائيات (للأدمن فقط) ====================
    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        from flask import jsonify
        from .db import get_db
        
        db = get_db()
        total_users = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        total_martyrs = db.execute('SELECT COUNT(*) as count FROM martyrs').fetchone()['count']
        
        return jsonify({
            'users': total_users,
            'donations': 0,
            'expenses': 0,
            'martyrs': total_martyrs
        })

    return app
