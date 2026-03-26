import os
import random
import string
import logging
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import User, Donation, Expense, Martyr, ResetCode
from app.helpers import send_reset_code_sms, send_reset_code_telegram

logger = logging.getLogger(__name__)

# ==================== الصفحات العامة ====================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/transparency')
def transparency():
    """صفحة الشفافية"""
    return render_template('transparency.html')

@app.route('/martyrs')
def martyrs():
    """صفحة الشهداء"""
    martyrs_list = Martyr.query.all()
    return render_template('martyrs.html', martyrs=martyrs_list)

# ==================== مسارات المصادقة (Auth) ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(phone=phone).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash('تم تسجيل الدخول بنجاح', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('رقم الهاتف أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('public/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """تسجيل حساب جديد"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        college = request.form.get('college')
        specialization = request.form.get('specialization')
        monthly_donation = request.form.get('monthly_donation')
        custom_amount = request.form.get('custom_amount')
        
        # التحقق من وجود الرقم
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            flash('هذا الرقم مسجل مسبقاً. يرجى استخدام رقم آخر أو تسجيل الدخول', 'danger')
            return redirect(url_for('register'))
        
        # إنشاء حساب جديد
        new_user = User(
            full_name=full_name,
            phone=phone,
            password=generate_password_hash(password),
            college=college,
            specialization=specialization,
            role='user',
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # تسجيل الدخول تلقائياً
        login_user(new_user)
        
        flash('تم إنشاء الحساب بنجاح! مرحباً بك في نظام دعم الدفعة 109', 'success')
        return redirect(url_for('index'))
    
    return render_template('public/register.html')

@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET'])
def forgot_password():
    """صفحة نسيت كلمة السر"""
    return render_template('public/forgot_password.html')

# ==================== واجهات برمجية API ====================

@app.route('/api/check-phone', methods=['GET'])
def api_check_phone():
    """التحقق من وجود رقم الهاتف"""
    phone = request.args.get('phone')
    if not phone:
        return jsonify({'exists': False, 'error': 'Phone number required'}), 400
    
    user = User.query.filter_by(phone=phone).first()
    return jsonify({'exists': user is not None})

@app.route('/api/send-reset-code', methods=['POST'])
def api_send_reset_code():
    """إرسال كود استرجاع كلمة السر"""
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'success': False, 'message': 'رقم الهاتف مطلوب'}), 400
    
    # البحث عن المستخدم
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'success': False, 'message': 'لا يوجد حساب مسجل بهذا الرقم'}), 404
    
    # إنشاء كود عشوائي من 6 أرقام
    reset_code = ''.join(random.choices(string.digits, k=6))
    
    # حذف أي كود سابق للمستخدم
    ResetCode.query.filter_by(user_id=user.id).delete()
    
    # حفظ الكود الجديد مع صلاحية 10 دقائق
    new_code = ResetCode(
        user_id=user.id,
        code=reset_code,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.session.add(new_code)
    db.session.commit()
    
    # إرسال الكود عبر التيليجرام إذا كان مرتبطاً
    sent = False
    if user.telegram_id:
        try:
            from bot import send_reset_code_via_telegram
            send_reset_code_via_telegram(user.telegram_id, reset_code)
            sent = True
        except Exception as e:
            logger.error(f"Failed to send reset code via Telegram: {e}")
    
    # إرسال عبر SMS كبديل
    if not sent:
        try:
            send_reset_code_sms(phone, reset_code)
            sent = True
        except Exception as e:
            logger.error(f"Failed to send reset code via SMS: {e}")
    
    if sent:
        return jsonify({'success': True, 'message': 'تم إرسال كود التحقق'})
    else:
        return jsonify({'success': False, 'message': 'فشل إرسال الكود، يرجى المحاولة مرة أخرى'}), 500

@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """إعادة تعيين كلمة السر باستخدام الكود"""
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    new_password = data.get('new_password')
    
    if not all([phone, code, new_password]):
        return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'}), 400
    
    # البحث عن المستخدم
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'success': False, 'message': 'لا يوجد حساب مسجل بهذا الرقم'}), 404
    
    # التحقق من الكود
    reset_code = ResetCode.query.filter_by(user_id=user.id, code=code).first()
    if not reset_code:
        return jsonify({'success': False, 'message': 'كود التحقق غير صحيح'}), 400
    
    if reset_code.expires_at < datetime.utcnow():
        return jsonify({'success': False, 'message': 'انتهت صلاحية الكود. يرجى طلب كود جديد'}), 400
    
    # تحديث كلمة المرور
    user.password = generate_password_hash(new_password)
    
    # حذف الكود بعد الاستخدام
    db.session.delete(reset_code)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم تغيير كلمة المرور بنجاح'})

@app.route('/api/stats', methods=['GET'])
@login_required
def api_stats():
    """إحصائيات النظام (للأدمن فقط)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    total_users = User.query.count()
    total_donations = db.session.query(db.func.sum(Donation.amount)).filter_by(status='approved').scalar() or 0
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(status='approved').scalar() or 0
    total_martyrs = Martyr.query.count()
    
    return jsonify({
        'users': total_users,
        'donations': float(total_donations),
        'expenses': float(total_expenses),
        'martyrs': total_martyrs
    })

# ==================== مسارات المستخدم ====================

@app.route('/profile')
@login_required
def profile():
    """الملف الشخصي للمستخدم"""
    return render_template('profile.html', user=current_user)

@app.route('/my-donations')
@login_required
def my_donations():
    """تبرعات المستخدم"""
    donations = Donation.query.filter_by(user_id=current_user.id).order_by(Donation.created_at.desc()).all()
    return render_template('my_donations.html', donations=donations)

@app.route('/my-certificates')
@login_required
def my_certificates():
    """شهادات التبرع للمستخدم"""
    donations = Donation.query.filter_by(user_id=current_user.id, status='approved').all()
    return render_template('my_certificates.html', donations=donations)

@app.route('/donate')
def donate():
    """صفحة التبرع"""
    return render_template('donate.html')

# ==================== مسارات الأدمن ====================

@app.route('/admin')
@login_required
def admin_dashboard():
    """لوحة تحكم الأدمن"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin/dashboard.html')

@app.route('/admin/users')
@login_required
def admin_users():
    """إدارة المستخدمين"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/donations')
@login_required
def admin_donations():
    """إدارة التبرعات"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    donations = Donation.query.order_by(Donation.created_at.desc()).all()
    return render_template('admin/donations.html', donations=donations)

@app.route('/admin/expenses')
@login_required
def admin_expenses():
    """إدارة المصاريف"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    expenses = Expense.query.order_by(Expense.created_at.desc()).all()
    return render_template('admin/expenses.html', expenses=expenses)

@app.route('/admin/martyrs')
@login_required
def admin_martyrs():
    """إدارة الشهداء"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    martyrs = Martyr.query.all()
    return render_template('admin/martyrs.html', martyrs=martyrs)

@app.route('/admin/reports')
@login_required
def admin_reports():
    """التقارير"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin/reports.html')
