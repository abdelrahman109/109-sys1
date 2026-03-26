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
    
    # إنشاء جدول reset_codes
    with app.app_context():
        db = get_db(app)
        db.execute('''
            CREATE TABLE IF NOT EXISTS reset_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        ''')

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

    return app
