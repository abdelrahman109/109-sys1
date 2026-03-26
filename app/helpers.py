import os
import re
import uuid
import secrets
import csv
import io
from datetime import datetime, timedelta
from functools import wraps
from flask import flash, redirect, session, url_for, g, current_app, request, Response, send_file
from flask_login import current_user, login_required as flask_login_required
from werkzeug.utils import secure_filename
import locale

try:
    locale.setlocale(locale.LC_ALL, 'ar_EG.UTF-8')
except:
    pass

# ==================== تنسيق العملة ====================

def format_currency(amount):
    """تنسيق الأرقام كعملة (جنيه مصري)"""
    if amount is None:
        return "0 ج.م"
    try:
        return f"{int(amount):,} ج.م".replace(",", ".")
    except:
        return f"{amount} ج.م"

# ==================== دوال الأمان ====================

def generate_csrf_token():
    """توليد توكن CSRF"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

def ensure_csrf_token():
    """التأكد من وجود توكن CSRF في الجلسة"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return True

def validate_csrf(token):
    """التحقق من توكن CSRF"""
    return token and token == session.get('_csrf_token')

# ==================== دوال تحميل المستخدم ====================

def load_current_user(app):
    """تحميل المستخدم الحالي من قاعدة البيانات"""
    from flask import g, session
    from .models import User
    from .db import get_db
    
    user_id = session.get('user_id')
    if user_id:
        try:
            db = get_db(app)
            user_data = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            if user_data:
                g.current_user = User(user_data)
                return
        except Exception as e:
            print(f"Error loading user: {e}")
    
    g.current_user = None

# ==================== دوال المصادقة ====================

def login_required(f):
    """Decorator لتأكيد تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            flash('يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator لتأكيد صلاحيات الأدمن"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            flash('يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('auth.login'))
        if g.current_user.role != 'admin':
            flash('غير مصرح لك بالدخول إلى هذه الصفحة', 'danger')
            return redirect(url_for('auth.home'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator لتأكيد صلاحيات محددة"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            if g.current_user.role not in roles:
                flash('غير مصرح لك بالدخول إلى هذه الصفحة', 'danger')
                return redirect(url_for('auth.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== دوال رفع الملفات ====================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}

def allowed_file(filename):
    """التحقق من امتداد الملف المسموح"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_image_upload(file, upload_folder):
    """رفع صورة بشكل آمن"""
    if not file or not file.filename:
        return None, "لم يتم اختيار ملف"
    
    if not allowed_file(file.filename):
        return None, "نوع الملف غير مسموح"
    
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(upload_folder, unique_name)
    
    os.makedirs(upload_folder, exist_ok=True)
    
    try:
        file.save(filepath)
        return unique_name, None
    except Exception as e:
        return None, f"فشل رفع الملف: {str(e)}"

# ==================== دوال التقارير ====================

def csv_response(data, filename, fieldnames=None):
    """إنشاء استجابة CSV للتحميل"""
    output = io.StringIO()
    if fieldnames:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    else:
        writer = csv.writer(output)
        writer.writerows(data)
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}.csv'}
    )

def file_download_response(file_path, filename, as_attachment=True):
    """إنشاء استجابة لتحميل ملف"""
    return send_file(
        file_path,
        as_attachment=as_attachment,
        download_name=filename,
        mimetype='application/octet-stream'
    )

# ==================== دوال مساعدة عامة ====================

def generate_unique_code(prefix="DON", length=8):
    """توليد كود فريد"""
    random_part = secrets.token_hex(length // 2)[:length]
    return f"{prefix}{random_part.upper()}"

def validate_egyptian_phone(phone):
    """التحقق من صحة رقم الهاتف المصري"""
    pattern = r'^(010|011|012|015)[0-9]{8}$'
    return bool(re.match(pattern, phone))

def validate_email(email):
    """التحقق من صحة البريد الإلكتروني"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def get_client_ip():
    """الحصول على عنوان IP للعميل"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def generate_reset_code():
    """توليد كود استرجاع عشوائي من 6 أرقام"""
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def calculate_age(birth_date):
    """حساب العمر من تاريخ الميلاد"""
    if not birth_date:
        return None
    today = datetime.now().date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def donation_expiry(donation_date, expiry_minutes=10):
    """التحقق من انتهاء صلاحية التبرع"""
    if not donation_date:
        return False
    expiry_time = donation_date + timedelta(minutes=expiry_minutes)
    return datetime.now() > expiry_time

# ==================== دوال إضافية مطلوبة ====================

def ensure_dir(path):
    """التأكد من وجود المجلد، وإنشاؤه إذا لم يكن موجوداً"""
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def now_str():
    """إرجاع الوقت الحالي كسلسلة نصية"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
