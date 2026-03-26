from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint, g, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db
from .helpers import format_currency, load_current_user
import random
import string
from datetime import datetime, timedelta

# إنشاء Blueprint
bp = Blueprint('auth', __name__)

# ==================== الصفحات العامة ====================

@bp.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@bp.route('/transparency')
def transparency():
    """صفحة الشفافية"""
    return render_template('transparency.html')

@bp.route('/martyrs')
def martyrs():
    """صفحة الشهداء"""
    db = get_db(current_app)
    martyrs_list = db.execute('SELECT * FROM martyrs').fetchall()
    return render_template('martyrs.html', martyrs=martyrs_list)

# ==================== مسارات المصادقة ====================

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل الدخول"""
    if getattr(g, 'current_user', None) and g.current_user:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        db = get_db(current_app)
        user = db.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            # تسجيل الدخول
            from flask_login import login_user
            from .models import User
            user_obj = User(user)
            login_user(user_obj, remember=remember)
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('auth.index'))
        else:
            flash('رقم الهاتف أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('public/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """تسجيل حساب جديد"""
    if getattr(g, 'current_user', None) and g.current_user:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        db = get_db(current_app)
        
        # التحقق من وجود الرقم
        existing_user = db.execute('SELECT id FROM users WHERE phone = ?', (phone,)).fetchone()
        if existing_user:
            flash('هذا الرقم مسجل مسبقاً. يرجى استخدام رقم آخر أو تسجيل الدخول', 'danger')
            return redirect(url_for('auth.register'))
        
        # إنشاء حساب جديد
        hashed_password = generate_password_hash(password)
        db.execute(
            'INSERT INTO users (full_name, phone, password, role, created_at) VALUES (?, ?, ?, ?, ?)',
            (full_name, phone, hashed_password, 'user', datetime.now())
        )
        
        # تسجيل الدخول تلقائياً
        user = db.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
        from flask_login import login_user
        from .models import User
        login_user(User(user))
        
        flash('تم إنشاء الحساب بنجاح! مرحباً بك في نظام دعم الدفعة 109', 'success')
        return redirect(url_for('auth.index'))
    
    return render_template('public/register.html')

@bp.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.index'))

@bp.route('/forgot-password', methods=['GET'])
def forgot_password():
    """صفحة نسيت كلمة السر"""
    return render_template('public/forgot_password.html')

# ==================== واجهات برمجية API ====================

@bp.route('/api/check-phone', methods=['GET'])
def api_check_phone():
    """التحقق من وجود رقم الهاتف"""
    phone = request.args.get('phone')
    if not phone:
        return jsonify({'exists': False, 'error': 'Phone number required'}), 400
    
    db = get_db(current_app)
    user = db.execute('SELECT id FROM users WHERE phone = ?', (phone,)).fetchone()
    return jsonify({'exists': user is not None})

@bp.route('/api/send-reset-code', methods=['POST'])
def api_send_reset_code():
    """إرسال كود استرجاع كلمة السر"""
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'success': False, 'message': 'رقم الهاتف مطلوب'}), 400
    
    db = get_db(current_app)
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
    
    print(f"Reset code for {phone}: {reset_code}")
    
    return jsonify({'success': True, 'message': 'تم إرسال كود التحقق'})

@bp.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """إعادة تعيين كلمة السر"""
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    new_password = data.get('new_password')
    
    if not all([phone, code, new_password]):
        return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'}), 400
    
    db = get_db(current_app)
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

@bp.route('/api/stats', methods=['GET'])
def api_stats():
    """إحصائيات النظام"""
    db = get_db(current_app)
    total_users = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    total_martyrs = db.execute('SELECT COUNT(*) as count FROM martyrs').fetchone()['count'] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='martyrs'").fetchone() else 0
    
    return jsonify({
        'users': total_users,
        'donations': 0,
        'expenses': 0,
        'martyrs': total_martyrs
    })

# ==================== مسارات المستخدم ====================

@bp.route('/profile')
@login_required
def profile():
    """الملف الشخصي"""
    return render_template('profile.html', user=current_user)

@bp.route('/my-donations')
@login_required
def my_donations():
    """تبرعات المستخدم"""
    db = get_db(current_app)
    donations = db.execute(
        'SELECT * FROM donations WHERE user_id = ? ORDER BY created_at DESC',
        (current_user.id,)
    ).fetchall()
    return render_template('my_donations.html', donations=donations)

@bp.route('/my-certificates')
@login_required
def my_certificates():
    """شهادات المستخدم"""
    db = get_db(current_app)
    donations = db.execute(
        'SELECT * FROM donations WHERE user_id = ? AND status = "approved"',
        (current_user.id,)
    ).fetchall()
    return render_template('my_certificates.html', donations=donations)

@bp.route('/donate')
def donate():
    """صفحة التبرع"""
    return render_template('donate.html')

# ==================== مسارات الأدمن ====================

@bp.route('/admin')
@login_required
def admin_dashboard():
    """لوحة تحكم الأدمن"""
    if getattr(current_user, 'role', None) != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('auth.index'))
    return render_template('admin/dashboard.html')

@bp.route('/admin/users')
@login_required
def admin_users():
    """إدارة المستخدمين"""
    if getattr(current_user, 'role', None) != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('auth.index'))
    db = get_db(current_app)
    users = db.execute('SELECT * FROM users').fetchall()
    return render_template('admin/users.html', users=users)

@bp.route('/admin/donations')
@login_required
def admin_donations():
    """إدارة التبرعات"""
    if getattr(current_user, 'role', None) != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('auth.index'))
    db = get_db(current_app)
    donations = db.execute('SELECT * FROM donations ORDER BY created_at DESC').fetchall()
    return render_template('admin/donations.html', donations=donations)

@bp.route('/admin/expenses')
@login_required
def admin_expenses():
    """إدارة المصاريف"""
    if getattr(current_user, 'role', None) != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('auth.index'))
    return render_template('admin/expenses.html')

@bp.route('/admin/martyrs')
@login_required
def admin_martyrs():
    """إدارة الشهداء"""
    if getattr(current_user, 'role', None) != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('auth.index'))
    db = get_db(current_app)
    martyrs = db.execute('SELECT * FROM martyrs').fetchall()
    return render_template('admin/martyrs.html', martyrs=martyrs)

@bp.route('/admin/reports')
@login_required
def admin_reports():
    """التقارير"""
    if getattr(current_user, 'role', None) != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('auth.index'))
    return render_template('admin/reports.html')
