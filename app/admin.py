from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from .bot_service import notify_admins, send_telegram_message
from .constants import ADMIN_ROLES, DONATION_TYPES, EXPENSE_CATEGORIES, EXPENSE_PAYMENT_METHODS, MARTYR_PRIORITIES, PAYMENT_METHODS, SUPPORT_TYPES
from .db import (
    add_expense,
    add_martyr_support,
    audit,
    create_backup,
    create_broadcast_log,
    create_martyr,
    dashboard_stats,
    get_colleges,
    get_donation,
    get_martyr,
    get_system_health,
    get_weapons_by_college,
    list_audit_logs,
    list_broadcast_messages,
    list_donations,
    list_expenses,
    list_martyr_support_logs,
    list_martyrs,
    list_notification_logs,
    list_users,
    review_donation,
    review_expense,
    telegram_recipients,
    update_martyr,
    update_martyr_image,
    update_user_admin,
)
from .helpers import admin_required, login_required, role_required, secure_image_upload

bp = Blueprint('admin', __name__, url_prefix='/admin')


def _martyr_form_data(form):
    def to_int(name, default=0):
        try:
            return int(form.get(name) or default)
        except Exception:
            return default
    def nullable_int(name):
        value = (form.get(name) or '').strip()
        return int(value) if value else None
    def nullable_text(name):
        value = (form.get(name) or '').strip()
        return value or None
    def nullable_float(name):
        value = (form.get(name) or '').strip()
        try:
            return float(value) if value else None
        except Exception:
            return None
    sons = to_int('sons_count')
    daughters = to_int('daughters_count')
    return {
        'full_name': form.get('full_name', '').strip(),
        'military_rank': nullable_text('military_rank'),
        'college_id': nullable_int('college_id'),
        'weapon_id': nullable_int('weapon_id'),
        'custom_weapon': nullable_text('custom_weapon'),
        'governorate': nullable_text('governorate'),
        'birth_date': nullable_text('birth_date'),
        'martyrdom_date': nullable_text('martyrdom_date'),
        'age_at_martyrdom': nullable_float('age_at_martyrdom'),
        'marital_status': nullable_text('marital_status'),
        'brothers_count': to_int('brothers_count'),
        'sisters_count': to_int('sisters_count'),
        'sons_count': sons,
        'daughters_count': daughters,
        'children_count': to_int('children_count', sons + daughters),
        'father_phone': nullable_text('father_phone'),
        'mother_phone': nullable_text('mother_phone'),
        'alternate_phone': nullable_text('alternate_phone'),
        'alternate_phone_owner': nullable_text('alternate_phone_owner'),
        'family_guardian_name': nullable_text('family_guardian_name'),
        'family_phone': nullable_text('family_phone'),
        'family_address': nullable_text('family_address'),
        'monthly_support_needed': to_int('monthly_support_needed'),
        'urgent_need': 1 if form.get('urgent_need') else 0,
        'support_priority': form.get('support_priority') or 'normal',
        'family_status': nullable_text('family_status'),
        'notes': nullable_text('notes'),
        'is_active': 1 if form.get('is_active', '1') in ('1', 'on', 'true') else 0,
        'image_path': None,
    }


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = dashboard_stats(current_app)
    health = get_system_health(current_app)
    pending = list_donations(current_app, status='pending_review')[:10]
    expenses = list_expenses(current_app, status='pending')[:10]
    martyrs = list_martyrs(current_app, is_active=1)[:8]
    return render_template('admin/dashboard.html', stats=stats, health=health, pending=pending, expenses=expenses, martyrs=martyrs)


@bp.route('/users')
@login_required
@role_required('super_admin')
def users():
    q = request.args.get('q', '').strip()
    return render_template('admin/users.html', users=list_users(current_app, q), q=q, roles=ADMIN_ROLES)


@bp.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
@role_required('super_admin')
def update_user(user_id):
    role = request.form.get('role', 'donor')
    is_active = 1 if request.form.get('is_active') else 0
    is_verified = 1 if request.form.get('is_verified') else 0
    update_user_admin(current_app, user_id, role, is_active, is_verified)
    audit(current_app, session['user_id'], 'update_user_admin', 'user', user_id, f'role={role}, active={is_active}, verified={is_verified}', request.remote_addr)
    flash('تم تحديث بيانات المستخدم', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/donations')
@login_required
@role_required('super_admin', 'finance_admin', 'reviewer')
def donations():
    filters = {
        'status': request.args.get('status', '').strip(),
        'donation_type': request.args.get('donation_type', '').strip(),
        'payment_method': request.args.get('payment_method', '').strip(),
        'college_id': request.args.get('college_id', '').strip(),
        'q': request.args.get('q', '').strip(),
    }
    rows = list_donations(current_app, status=filters['status'] or None, donation_type=filters['donation_type'] or None, payment_method=filters['payment_method'] or None, college_id=int(filters['college_id']) if filters['college_id'] else None, q=filters['q'] or None)
    return render_template('admin/donations.html', donations=rows, filters=filters, donation_types=DONATION_TYPES, payment_methods=PAYMENT_METHODS, colleges=get_colleges(current_app))


@bp.route('/donations/<int:donation_id>/approve', methods=['POST'])
@login_required
@role_required('super_admin', 'finance_admin', 'reviewer')
def approve_donation(donation_id):
    notes = request.form.get('admin_notes', '').strip() or None
    review_donation(current_app, donation_id, session['user_id'], 'paid', None, notes)
    donation = get_donation(current_app, donation_id)
    if donation and donation.get('telegram_chat_id'):
        send_telegram_message(current_app, donation['telegram_chat_id'], f"تم قبول تبرعك بنجاح\nالكود: {donation['donation_code']}\nالمبلغ: {donation['amount']} جنيه", donation['user_id'], 'donation_approved')
    audit(current_app, session['user_id'], 'approve_donation', 'donation', donation_id, donation['donation_code'] if donation else '', request.remote_addr)
    flash('تم قبول التبرع', 'success')
    return redirect(url_for('admin.donations'))


@bp.route('/donations/<int:donation_id>/reject', methods=['POST'])
@login_required
@role_required('super_admin', 'finance_admin', 'reviewer')
def reject_donation(donation_id):
    reason = request.form.get('reason', '').strip() or 'تم الرفض بواسطة الأدمن'
    notes = request.form.get('admin_notes', '').strip() or None
    review_donation(current_app, donation_id, session['user_id'], 'rejected', reason, notes)
    donation = get_donation(current_app, donation_id)
    if donation and donation.get('telegram_chat_id'):
        send_telegram_message(current_app, donation['telegram_chat_id'], f"تم رفض التبرع\nالكود: {donation['donation_code']}\nالسبب: {reason}", donation['user_id'], 'donation_rejected')
    audit(current_app, session['user_id'], 'reject_donation', 'donation', donation_id, reason, request.remote_addr)
    flash('تم رفض التبرع', 'warning')
    return redirect(url_for('admin.donations'))


@bp.route('/martyrs')
@login_required
@role_required('super_admin', 'family_admin', 'finance_admin')
def martyrs():
    filters = {
        'q': request.args.get('q', '').strip(),
        'college_id': request.args.get('college_id', '').strip(),
        'priority': request.args.get('priority', '').strip(),
        'is_active': request.args.get('is_active', '1').strip(),
    }
    rows = list_martyrs(
        current_app,
        q=filters['q'] or None,
        college_id=int(filters['college_id']) if filters['college_id'] else None,
        priority=filters['priority'] or None,
        is_active=int(filters['is_active']) if filters['is_active'] in ('0', '1') else None,
    )
    return render_template('admin/martyrs.html', martyrs=rows, filters=filters, colleges=get_colleges(current_app), priorities=MARTYR_PRIORITIES)


@bp.route('/martyrs/new', methods=['GET', 'POST'])
@login_required
@role_required('super_admin', 'family_admin')
def martyr_create():
    if request.method == 'POST':
        data = _martyr_form_data(request.form)
        if not data['full_name']:
            flash('الاسم مطلوب', 'danger')
            return redirect(url_for('admin.martyr_create'))
        martyr_id = create_martyr(current_app, data)
        image = request.files.get('image')
        if image and image.filename:
            filename, error = secure_image_upload(image, current_app.config['MARTYR_UPLOAD_FOLDER'])
            if not error:
                update_martyr_image(current_app, martyr_id, f'uploads/martyrs/{filename}')
        audit(current_app, session['user_id'], 'create_martyr', 'martyr', martyr_id, data['full_name'], request.remote_addr)
        flash('تمت إضافة الشهيد', 'success')
        return redirect(url_for('admin.martyr_detail', martyr_id=martyr_id))
    return render_template('admin/martyr_form.html', martyr=None, colleges=get_colleges(current_app), priorities=MARTYR_PRIORITIES, weapons=[], support_types=SUPPORT_TYPES)


@bp.route('/martyrs/<int:martyr_id>', methods=['GET', 'POST'])
@login_required
@role_required('super_admin', 'family_admin', 'finance_admin')
def martyr_detail(martyr_id):
    martyr = get_martyr(current_app, martyr_id)
    if not martyr:
        flash('السجل غير موجود', 'danger')
        return redirect(url_for('admin.martyrs'))
    if request.method == 'POST':
        data = _martyr_form_data(request.form)
        if not data['full_name']:
            flash('الاسم مطلوب', 'danger')
            return redirect(url_for('admin.martyr_detail', martyr_id=martyr_id))
        update_martyr(current_app, martyr_id, data)
        image = request.files.get('image')
        if image and image.filename:
            filename, error = secure_image_upload(image, current_app.config['MARTYR_UPLOAD_FOLDER'])
            if error:
                flash(error, 'danger')
                return redirect(url_for('admin.martyr_detail', martyr_id=martyr_id))
            update_martyr_image(current_app, martyr_id, f'uploads/martyrs/{filename}')
        audit(current_app, session['user_id'], 'update_martyr', 'martyr', martyr_id, data['full_name'], request.remote_addr)
        flash('تم تحديث البيانات', 'success')
        return redirect(url_for('admin.martyr_detail', martyr_id=martyr_id))
    weapons = get_weapons_by_college(current_app, martyr['college_id']) if martyr.get('college_id') else []
    logs = list_martyr_support_logs(current_app, martyr_id)
    return render_template('admin/martyr_detail.html', martyr=get_martyr(current_app, martyr_id), weapons=weapons, colleges=get_colleges(current_app), priorities=MARTYR_PRIORITIES, logs=logs, support_types=SUPPORT_TYPES)


@bp.route('/martyrs/<int:martyr_id>/support', methods=['POST'])
@login_required
@role_required('super_admin', 'family_admin', 'finance_admin')
def martyr_support_add(martyr_id):
    add_martyr_support(
        current_app,
        martyr_id,
        request.form.get('support_type') or 'دعم مالي',
        int(request.form.get('amount') or 0),
        request.form.get('support_date') or '',
        request.form.get('description', '').strip(),
        session['user_id'],
    )
    audit(current_app, session['user_id'], 'add_martyr_support', 'martyr', martyr_id, request.form.get('description', ''), request.remote_addr)
    flash('تم إضافة سجل الدعم', 'success')
    return redirect(url_for('admin.martyr_detail', martyr_id=martyr_id))


@bp.route('/expenses', methods=['GET', 'POST'])
@login_required
@role_required('super_admin', 'finance_admin')
def expenses():
    martyrs = list_martyrs(current_app, is_active=1)
    if request.method == 'POST':
        receipt_path = None
        amount = int(request.form['amount'])
        receipt = request.files.get('receipt')
        if amount >= current_app.config['EXPENSE_RECEIPT_REQUIRED_OVER'] and (not receipt or not receipt.filename):
            flash('يجب رفع إيصال للمبالغ الكبيرة', 'danger')
            return redirect(url_for('admin.expenses'))
        if receipt and receipt.filename:
            filename, error = secure_image_upload(receipt, current_app.config['EXPENSE_UPLOAD_FOLDER'])
            if error:
                flash(error, 'danger')
                return redirect(url_for('admin.expenses'))
            receipt_path = f'uploads/expense_receipts/{filename}'
        martyr_id = int(request.form['martyr_id']) if request.form.get('martyr_id') else None
        add_expense(current_app, request.form['expense_date'], request.form['category'], amount, request.form.get('description', '').strip(), request.form['payment_method'], session['user_id'], receipt_path, martyr_id)
        audit(current_app, session['user_id'], 'add_expense', 'expense', None, request.form.get('description', ''), request.remote_addr)
        flash('تمت إضافة المصروف بحالة انتظار اعتماد', 'success')
        return redirect(url_for('admin.expenses'))
    status = request.args.get('status', '').strip() or None
    return render_template('admin/expenses.html', expenses=list_expenses(current_app, status=status), categories=EXPENSE_CATEGORIES, payment_methods=EXPENSE_PAYMENT_METHODS, selected_status=status, martyrs=martyrs)


@bp.route('/expenses/<int:expense_id>/approve', methods=['POST'])
@login_required
@role_required('super_admin', 'finance_admin')
def approve_expense(expense_id):
    review_expense(current_app, expense_id, 'approved', session['user_id'])
    audit(current_app, session['user_id'], 'approve_expense', 'expense', expense_id, '', request.remote_addr)
    flash('تم اعتماد المصروف', 'success')
    return redirect(url_for('admin.expenses'))


@bp.route('/expenses/<int:expense_id>/reject', methods=['POST'])
@login_required
@role_required('super_admin', 'finance_admin')
def reject_expense(expense_id):
    reason = request.form.get('reason', '').strip() or 'تم رفض المصروف'
    review_expense(current_app, expense_id, 'rejected', session['user_id'], reason)
    audit(current_app, session['user_id'], 'reject_expense', 'expense', expense_id, reason, request.remote_addr)
    flash('تم رفض المصروف', 'warning')
    return redirect(url_for('admin.expenses'))


@bp.route('/broadcast', methods=['GET', 'POST'])
@login_required
@role_required('super_admin', 'content_admin')
def broadcast():
    history = list_broadcast_messages(current_app)
    if request.method == 'POST':
        title = request.form['title'].strip()
        body = request.form['body'].strip()
        recipients = telegram_recipients(current_app)
        success_count = 0
        for recipient in recipients:
            ok, _ = send_telegram_message(current_app, recipient['telegram_chat_id'], f"{title}\n\n{body}", recipient['id'], title)
            if ok:
                success_count += 1
        create_broadcast_log(current_app, title, body, session['user_id'], len(recipients), success_count)
        audit(current_app, session['user_id'], 'broadcast', 'broadcast', None, f'{title} -> {success_count}/{len(recipients)}', request.remote_addr)
        flash(f'تم إرسال الرسالة إلى {success_count} من أصل {len(recipients)} مستلم', 'success')
        return redirect(url_for('admin.broadcast'))
    return render_template('admin/broadcast.html', history=history)


@bp.route('/audit-logs')
@login_required
@role_required('super_admin')
def audit_logs():
    return render_template('admin/audit_logs.html', logs=list_audit_logs(current_app))


@bp.route('/notification-logs')
@login_required
@role_required('super_admin', 'content_admin')
def notification_logs():
    return render_template('admin/notification_logs.html', logs=list_notification_logs(current_app))


@bp.route('/system')
@login_required
@role_required('super_admin')
def system_health():
    return render_template('admin/system.html', health=get_system_health(current_app))


@bp.route('/system/backup', methods=['POST'])
@login_required
@role_required('super_admin')
def system_backup():
    backup_path = create_backup(current_app)
    audit(current_app, session['user_id'], 'manual_backup', 'system', None, backup_path, request.remote_addr)
    notify_admins(current_app, f'تم إنشاء نسخة احتياطية جديدة\n{backup_path}', 'backup')
    flash('تم إنشاء النسخة الاحتياطية بنجاح', 'success')
    return redirect(url_for('admin.system_health'))

@bp.route('/transparency')
@login_required
@role_required('super_admin', 'finance_admin')
def transparency():
    """صفحة الشفافية للأدمن فقط"""
    return render_template('admin/transparency.html')


@bp.route('/api/transparency-data')
@login_required
@role_required('super_admin', 'finance_admin')
def api_transparency_data():
    """API بيانات الشفافية"""
    db = get_db(current_app)
    
    total_donations = db.execute('SELECT SUM(amount) as total FROM donations WHERE status = "approved"').fetchone()['total'] or 0
    total_expenses = db.execute('SELECT SUM(amount) as total FROM expenses WHERE status = "approved"').fetchone()['total'] or 0
    
    donations = db.execute('''
        SELECT d.*, u.full_name as user_name 
        FROM donations d 
        LEFT JOIN users u ON d.user_id = u.id 
        WHERE d.status = "approved" 
        ORDER BY d.created_at DESC 
        LIMIT 20
    ''').fetchall()
    
    expenses = db.execute('''
        SELECT * FROM expenses 
        WHERE status = "approved" 
        ORDER BY created_at DESC 
        LIMIT 20
    ''').fetchall()
    
    return jsonify({
        'total_donations': float(total_donations),
        'total_expenses': float(total_expenses),
        'donations': [dict(d) for d in donations],
        'expenses': [dict(e) for e in expenses]
    })
